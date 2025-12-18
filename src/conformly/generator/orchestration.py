from typing import Any

from .registry import get_generator

from conformly.specs import FieldSpec, ModelSpec


def generate_valid(model_spec: ModelSpec) -> dict[str, Any]:
    return {
        field.name: generate_field(field, valid=True) for field in model_spec.fields
    }


def generate_invalid(model_spec: ModelSpec, field_index: int) -> dict[str, Any]:
    return {
        field.name: (
            generate_field(field, valid=False)
            if i == field_index and len(field.constraints) >= 1
            else generate_field(field, valid=True)
        )
        for i, field in enumerate(model_spec.fields)
    }


def generate_field(field_spec: FieldSpec, valid: bool) -> Any:
    if field_spec.is_optional() and (valid or not field_spec.constraints):
        return None

    if field_spec.has_default() and valid:
        return field_spec.default

    return get_generator(field_spec).generate_value(field_spec.constraints, valid)
