from dataclasses import MISSING, Field, fields, is_dataclass
from enum import Enum
from types import UnionType
from typing import (
    Annotated,
    Any,
    Literal,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from ...constraints import Constraint, OneOf
from ...constraints.mapping import create_constraint
from ...constraints.types import ALLOWED_CONSTRAINT_TYPE, ConstraintType
from ...specs import FieldSpec, ModelSpec
from ...types import _UNSET

UNION_TYPES = (Union, UnionType)


def supports(model: type) -> bool:
    return is_dataclass(model)


def parse(model: type) -> ModelSpec:
    if not supports(model):
        raise TypeError(f"Unsupported model type: {model}. Expected dataclass.")

    return ModelSpec(name=model.__name__, type="dataclass", fields=parse_fields(model))


def parse_fields(model: type) -> tuple[FieldSpec, ...]:
    type_hints = get_type_hints(model, include_extras=True)
    return tuple(
        parse_field(field, resolve_type(type_hints, field.name))
        for field in fields(model)
    )


def resolve_type(type_hints: dict[str, Any], field_name: str) -> Any:
    return type_hints[field_name]


def parse_field(field: Field[Any], field_type: Any) -> FieldSpec:
    base_type = unwrap_base_type(field_type)

    nested_model = None
    if supports(base_type):
        nested_model = parse(base_type)

    return FieldSpec(
        name=field.name,
        type=base_type,
        constraints=parse_constraints(field, field_type),
        default=parse_defaults(field),
        nullable=is_nullable(field_type),
        nested_model=nested_model,
    )


def unwrap_base_type(field_type: Any) -> Any:
    t = field_type

    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    if get_origin(t) in UNION_TYPES:
        args = get_args(t)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) >= 2:
            t = args[0]
        else:
            raise TypeError(
                f"Invalid field type: {field_type!r}. "
                "Only Optional[T], Union[T, None] is supported. "
                f"Got Union[{', '.join(a.__name__ for a in non_none)}]"
            )

    return t


def is_nullable(field_type: Any) -> bool:
    t = field_type

    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    origin = get_origin(t)

    if origin in UNION_TYPES:
        return type(None) in get_args(t)

    return False


def parse_defaults(field: Field[Any]) -> Any:
    if field.default is not MISSING:
        return field.default

    elif field.default_factory is not MISSING:
        return field.default_factory

    return _UNSET


def parse_constraints(field: Field[Any], field_type: Any) -> tuple[Constraint, ...]:
    constraints = (
        *parse_annotated_constraints(field_type),
        *parse_metadata_constraints(field),
        *parse_intrinsic_type_constraints(field_type),
    )
    if not is_constraints_consistent(constraints):
        raise TypeError(
            f"Field '{field.name}': Literal/Enum types define a closed set of values "
            f"and cannot be combined with other constraints. "
            f"Found conflicting constraints: {[type(c).__name__ for c in constraints]}"
        )
    return constraints


def is_constraints_consistent(constraints: tuple[Constraint, ...]) -> bool:
    has_one_of = any(isinstance(c, OneOf) for c in constraints)
    return not has_one_of or len(constraints) == 1


def parse_annotated_constraints(field_type: Any) -> tuple[Constraint, ...]:
    if get_origin(field_type) is Annotated:
        args = get_args(field_type)
        metadata = args[1:]

        constraints = []
        for item in metadata:
            constraint = _metadata_to_constraints(item)
            if constraint:
                constraints.append(constraint)

        return tuple(constraints)

    return ()


def parse_metadata_constraints(field: Field[Any]) -> tuple[Constraint, ...]:
    if not field.metadata:
        return ()

    constraints = []
    for k, v in field.metadata.items():
        if k.startswith("_"):
            continue

        _validate_constraint_type(k)

        constraint = create_constraint(constraint_type=k, value=v)
        constraints.append(constraint)

    return tuple(constraints)


def parse_intrinsic_type_constraints(field_type: Any) -> tuple[Constraint, ...]:
    base_type = unwrap_base_type(
        field_type
    )  # NOTE: needed to find non consistent constraints

    if get_origin(base_type) is Literal:
        return (OneOf(get_args(base_type)),)

    if isinstance(base_type, type) and issubclass(base_type, Enum):
        return (OneOf(tuple(member.value for member in base_type)),)

    return ()


def _coerce_constraint_value(k: ConstraintType, v: Any) -> Any:
    if k == "pattern":
        return str(v)

    if k in ("min_length", "max_length"):
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            s = v.strip()
            try:
                return int(s)
            except ValueError as e:
                raise ValueError(f"Constraint {k!r} expects int, got {v!r}") from e
        raise ValueError(f"Constraint {k!r} expects int, got {type(v).__name__}")

    if k in ("gt", "ge", "lt", "le"):
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            s = v.strip()
            try:
                if all(ch.isdigit() for ch in s.lstrip("+-")):
                    return int(s)
                return float(s)
            except ValueError as e:
                raise ValueError(f"Constraint {k!r} expects number, got {v!r}") from e
        raise ValueError(f"Constraint {k!r} expects number, got {type(v).__name__}")


def _metadata_to_constraints(metadata_item: Any) -> Constraint | None:
    match metadata_item:
        case Constraint():
            return metadata_item
        case str() if "=" in metadata_item:
            k, v = metadata_item.split("=", 1)
            k_validated = _validate_constraint_type(k)
            v_coerced = _coerce_constraint_value(k_validated, v)
            return create_constraint(k_validated, v_coerced)
        case str():
            k_validated = _validate_constraint_type(metadata_item)
            return create_constraint(k_validated, True)
        case {"type": k, "value": v}:
            k_validated = _validate_constraint_type(k)
            v_coerced = _coerce_constraint_value(k_validated, v)
            return create_constraint(k_validated, v_coerced)
        case _:
            return None


def _validate_constraint_type(k: str) -> ConstraintType:
    if k not in ALLOWED_CONSTRAINT_TYPE:
        raise ValueError(f"Unknown constraint type {k!r}")
    return cast("ConstraintType", k)
