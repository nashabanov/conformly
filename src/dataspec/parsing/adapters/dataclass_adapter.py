from dataclasses import MISSING, Field, fields, is_dataclass
from typing import Annotated, Any, get_origin, get_type_hints

from dataspec.specs import ConstraintSpec, FieldSpec, ModelSpec


def supports(model: type) -> bool:
    return is_dataclass(model)


def parse(model: type) -> ModelSpec:
    return ModelSpec(
        name=parse_name(model), type="dataclass", fields=parse_fields(model)
    )


def parse_name(model: type) -> str:
    return model.__name__


def parse_fields(model: type) -> list[FieldSpec]:
    type_hints = get_type_hints(model, include_extras=True)
    return [parse_field(field, type_hints[field.name]) for field in fields(model)]


def parse_field(field: Field[Any], field_type: type) -> FieldSpec:
    return FieldSpec(name=field.name, type=field_type)


def parse_defaults(field: Field[Any]) -> Any:
    if field.default is not MISSING:
        return field.default

    # TODO:решить нужно ли возвращать ленивую фабрику или сразу генерировать значения
    # (скорее всего ленивую и усложнять логику спеки)
    elif field.default_factory is not MISSING:
        return field.default_factory()

    return MISSING


def parse_constraints(field: Field[Any], field_type: type) -> list[ConstraintSpec]:
    return [
        *parse_annotated_constraints(field_type),
        *parse_metadata_constraints(field),
    ]


def parse_annotated_constraints(field_type: type) -> list[ConstraintSpec]:
    if get_origin(field_type) is Annotated:
        # TODO: реализовать парсинга аннотаций
        return []
    return []


def parse_metadata_constraints(field: Field[Any]) -> list[ConstraintSpec]:
    if field.metadata:
        # TODO: переложить dict в ConstraintSpec
        return []
    return []
