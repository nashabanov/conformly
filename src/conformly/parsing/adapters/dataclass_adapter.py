from dataclasses import MISSING, Field, fields, is_dataclass
from types import UnionType
from typing import Annotated, Any, Union, cast, get_args, get_origin, get_type_hints

from conformly.constraints import Constraint
from conformly.constraints.mapping import create_constraint
from conformly.constraints.types import ALLOWED_CONSTRAINT_TYPE, ConstraintType
from conformly.specs import FieldSpec, ModelSpec
from conformly.specs.field import _UNSET

UNION_TYPES = (Union, UnionType)


def supports(model: type) -> bool:
    return is_dataclass(model)


def parse(model: type) -> ModelSpec:
    if not supports(model):
        raise TypeError(f"Unsupported model type: {model}. Expected dataclass.")

    return ModelSpec(
        name=parse_name(model), type="dataclass", fields=parse_fields(model)
    )


def parse_name(model: type) -> str:
    return model.__name__


def parse_fields(model: type) -> list[FieldSpec]:
    type_hints = get_type_hints(model, include_extras=True)
    return [
        parse_field(field, resolve_type(type_hints, field.name))
        for field in fields(model)
    ]


def resolve_type(type_hints: dict[str, Any], field_name: str) -> Any:
    return type_hints[field_name]


def parse_field(field: Field[Any], field_type: Any) -> FieldSpec:
    return FieldSpec(
        name=field.name,
        type=unwrap_annotated(field_type),
        constraints=parse_constraints(field, field_type),
        default=parse_defaults(field),
        nullable=is_nullable(field_type),
    )


def unwrap_annotated(field_type: Any) -> Any:
    if get_origin(field_type) is Annotated:
        return get_args(field_type)[0]
    return field_type


def is_nullable(field_type: Any) -> bool:
    unwrapped = unwrap_annotated(field_type)
    origin = get_origin(unwrapped)
    if origin in UNION_TYPES:
        return type(None) in get_args(unwrapped)
    return False


def parse_defaults(field: Field[Any]) -> Any:
    if field.default is not MISSING:
        return field.default

    elif field.default_factory is not MISSING:
        return field.default_factory

    return _UNSET


def parse_constraints(field: Field[Any], field_type: Any) -> list[Constraint]:
    return [
        *parse_annotated_constraints(field_type),
        *parse_metadata_constraints(field),
    ]


def parse_annotated_constraints(field_type: Any) -> list[Constraint]:
    if get_origin(field_type) is Annotated:
        args = get_args(field_type)
        metadata = args[1:]

        constraints = []
        for item in metadata:
            constraint = _metadata_to_constraints(item)
            if constraint:
                constraints.append(constraint)

        return constraints

    return []


def parse_metadata_constraints(field: Field[Any]) -> list[Constraint]:
    if not field.metadata:
        return []

    constraints = []
    for k, v in field.metadata.items():
        if k.startswith("_"):
            continue

        _validate_constraint_type(k)

        constraint = create_constraint(constraint_type=k, value=v)
        constraints.append(constraint)

    return constraints


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
