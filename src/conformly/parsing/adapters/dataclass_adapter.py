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
from ...types import _UNSET, ENUMERATED_TYPE

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
    runtime_type, intrinsic_constraints = extract_runtime_type_and_constraints(
        field_type, field.name
    )

    external_constraints = (
        *parse_annotated_constraints(field_type),
        *parse_metadata_constraints(field),
    )

    all_constraints = (*intrinsic_constraints, *external_constraints)
    if not is_constraints_consistent(all_constraints):
        raise TypeError(
            f"Field '{field.name}': closed set (Literal/Enum) defines a fixed "
            f"set of values and cannot be combined with other constraints. "
            f"Conflicting constraints: {[type(c).__name__ for c in all_constraints]}"
        )

    nested_model = (
        parse(runtime_type)
        if runtime_type is not ENUMERATED_TYPE and supports(runtime_type)
        else None
    )

    return FieldSpec(
        name=field.name,
        type=runtime_type,
        constraints=all_constraints,
        default=parse_defaults(field),
        nullable=is_nullable(field_type),
        nested_model=nested_model,
    )


def extract_runtime_type_and_constraints(
    field_type: Any, field_name: str
) -> tuple[type, tuple[Constraint, ...]]:
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
                f"Field '{field_name}': unsupported union type {field_type!r}. "
                "Only Optional[T] (Union[T, None]) is allowed."
            )

    if get_origin(t) is Literal:
        values = get_args(t)
        if not values:
            raise TypeError(
                f"Field '{field_name}': empty Literal[] is not allowed. "
                "Must specify at least one value."
            )
        return ENUMERATED_TYPE, (OneOf(values),)

    if isinstance(t, type) and issubclass(t, Enum):
        members = list(t)
        if not members:
            raise TypeError(
                f"Field '{field_name}': empty Enum {t.__name__} is not allowed. "
                "Must define at least one member."
            )
        values = tuple(member.value for member in members)
        return ENUMERATED_TYPE, (OneOf(values),)

    if isinstance(t, type):
        return t, ()

    raise TypeError(f"Field '{field_name}': unsupported type annotation {field_type!r}")


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
