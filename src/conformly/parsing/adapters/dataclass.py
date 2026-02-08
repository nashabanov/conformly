from dataclasses import MISSING, Field, fields, is_dataclass
from typing import (
    Any,
    get_type_hints,
)

from ...specs import FieldSpec, ModelSpec
from ...types import _UNSET, ENUMERATED_TYPE
from ..constraints import (
    is_constraints_consistent,
    parse_annotated_constraints,
    parse_metadata_constraints,
)
from ..type_analysis import extract_runtime_type_and_constraints, is_nullable


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
        *parse_metadata_constraints(field.metadata),
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


def parse_defaults(field: Field[Any]) -> Any:
    if field.default is not MISSING:
        return field.default

    elif field.default_factory is not MISSING:
        return field.default_factory

    return _UNSET
