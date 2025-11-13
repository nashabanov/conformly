from dataclasses import MISSING, Field, fields, is_dataclass
from types import UnionType
from typing import Annotated, Any, Union, get_args, get_origin, get_type_hints

from dataspec.specs import ConstraintSpec, FieldSpec, ModelSpec
from dataspec.specs.field import _UNSET

UNION_TYPES = (Union, UnionType)

ALLOWED_CONSTRAINT_TYPE = ["min", "max", "pattern", "length"]

# TODO: Предусмотреть кейс Annotated(Optional[str], ...)


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
        type=field_type,
        constraints=parse_constraints(field, field_type),
        default=parse_defaults(field),
        nullable=is_nullable(field_type),
    )


def is_nullable(field_type: Any) -> bool:
    origin = get_origin(field_type)
    if origin in UNION_TYPES:
        return type(None) in get_args(field_type)
    return False


def parse_defaults(field: Field[Any]) -> Any:
    if field.default is not MISSING:
        return field.default

    # TODO:решить нужно ли возвращать ленивую фабрику или сразу генерировать значения
    # (скорее всего ленивую и усложнять логику спеки)
    elif field.default_factory is not MISSING:
        return field.default_factory()

    return _UNSET


def parse_constraints(field: Field[Any], field_type: Any) -> list[ConstraintSpec]:
    return [
        *parse_annotated_constraints(field_type),
        *parse_metadata_constraints(field),
    ]


def parse_annotated_constraints(field_type: Any) -> list[ConstraintSpec]:
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


def parse_metadata_constraints(field: Field[Any]) -> list[ConstraintSpec]:
    if not field.metadata:
        return []

    constraints = []
    for k, v in field.metadata.items():
        if k.startswith("_"):
            continue

        _validate_constraint_type(k)

        constraint = ConstraintSpec(constraint_type=k, value=v)
        constraints.append(constraint)

    return constraints


def _metadata_to_constraints(metadata_item: Any) -> ConstraintSpec | None:
    match metadata_item:
        case ConstraintSpec():
            return metadata_item
        case str() if "=" in metadata_item:
            k, v = metadata_item.split("=", 1)
            _validate_constraint_type(k)
            return ConstraintSpec(k, v)
        case str():
            _validate_constraint_type(metadata_item)
            return ConstraintSpec(metadata_item, True)
        case {"type": k, "value": v}:
            _validate_constraint_type(k)
            return ConstraintSpec(k, v)
        case _:
            return None


def _validate_constraint_type(k: str) -> None:
    if k not in ALLOWED_CONSTRAINT_TYPE:
        raise ValueError(f"Uknown constraint type {k!r}")
