import random
from typing import Any

from dataspec.specs import FieldSpec, ModelSpec


def generate(
    model_spec: ModelSpec, valid: bool = True
) -> dict[str, Any] | list[dict[str, Any]]:
    return generate_valid(model_spec) if valid else generate_invalid(model_spec)


def generate_valid(model_spec: ModelSpec) -> dict[str, Any]:
    return {
        field.name: generate_field(field, valid=True) for field in model_spec.fields
    }


def generate_invalid(model_spec: ModelSpec) -> list[dict[str, Any]]:
    return [{}, {}]


def generate_field(field_spec: FieldSpec, valid: bool) -> Any:
    if field_spec.is_optional():
        return None
    if field_spec.has_default():
        return field_spec.default

    field_type = field_spec.type

    if field_type is int:
        return 1
    elif field_type is str:
        return "abc"
    elif field_type is bool:
        return random.choice([True, False])
    else:
        raise NotImplementedError(
            f"Unsupported field type {field_spec.name}: {field_type}"
        )
