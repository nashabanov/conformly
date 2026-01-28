import random
from typing import Any

from ..planner import PlannedTask
from ..resolver import ResolvedField, ResolvedModel
from ..types import _UNSET, ViolationType
from .registry import get_generator


def generate_valid(model: ResolvedModel) -> dict[str, Any]:
    return {field.name: generate_field(field) for field in model.fields}


def generate_invalid(model: ResolvedModel, task: PlannedTask) -> dict[str, Any]:
    target_index = task.path[0]

    if not (0 <= target_index < len(model.fields)):
        raise IndexError(
            f"Path index {target_index} out of range for model "
            f"'{model.name}' with {len(model.fields)} fields"
        )

    result: dict[str, Any] = {}

    for i, field in enumerate(model.fields):
        if i != task.path[0]:
            result[field.name] = generate_field(field)
            continue

        if len(task.path) == 1:
            if len(task.allowed_violations) == 0:
                raise ValueError(f"Field '{field.name}' has no constraints to violate")
            result[field.name] = generate_field(field, task.allowed_violations)
            continue

        if field.nested_model is None:
            raise ValueError(f"Field '{field.name}' is not nested model")

        result[field.name] = generate_invalid(
            field.nested_model,
            PlannedTask(path=task.path[1:], allowed_violations=task.allowed_violations),
        )

    return result


def generate_field(
    field: ResolvedField, violations: tuple[ViolationType, ...] | None = None
) -> Any:
    if violations is None:
        if field.nullable:
            return None

        if field.default is not _UNSET:
            return field.default

    if field.nested_model:
        return generate_valid(field.nested_model)

    return get_generator(field.semantic.kind).generate_value(
        field.semantic, _choose_violation(violations)
    )


def _choose_violation(
    violations: tuple[ViolationType, ...] | None,
) -> ViolationType | None:
    if violations is None:
        return None

    return random.choice(violations)
