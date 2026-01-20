from typing import Any

from .registry import get_generator

from conformly.specs import FieldPath, FieldSpec, ModelSpec


def generate_valid(model_spec: ModelSpec) -> dict[str, Any]:
    return {
        field.name: generate_field(field, valid=True) for field in model_spec.fields
    }


def generate_invalid(model_spec: ModelSpec, field_path: FieldPath) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for i, field in enumerate(model_spec.fields):
        if i != field_path[0]:
            result[field.name] = generate_field(field, valid=True)
            continue

        if len(field_path) == 1:
            if not field.constraints:
                raise ValueError(f"Field '{field.name}' has no constraints to violate")
            result[field.name] = generate_field(field, valid=False)
            continue

        if field.nested_model is None:
            raise ValueError(f"Field '{field.name}' if not nested model")
        result[field.name] = generate_invalid(field.nested_model, field_path[1:])

    return result


def generate_field(field_spec: FieldSpec, valid: bool) -> Any:
    if field_spec.is_optional() and (valid or not field_spec.constraints):
        return None

    if field_spec.has_default() and valid:
        return field_spec.default

    if field_spec.nested_model:
        if not valid:
            raise AssertionError(
                "Invalid generation of nested field must be handled by generate_invalid"
            )
        return generate_valid(field_spec.nested_model)

    return get_generator(field_spec).generate_value(field_spec.constraints, valid)
