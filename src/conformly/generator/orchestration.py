import random
from typing import Any

from ..planner import PlannedTask
from ..resolver import ResolvedField, ResolvedModel, create_minimal_semantic
from ..types import _UNSET, ViolationType
from .registry import choose_mismatch_kind, choose_random_base_kind, get_generator


def generate_valid(model: ResolvedModel) -> dict[str, Any]:
    return {field.name: generate_field(field) for field in model.fields}


def generate_invalid(model: ResolvedModel, task: PlannedTask) -> dict[str, Any]:
    result: dict[str, Any] = {}

    target_index = task.path[0]

    if _is_extra_field(task, target_index, len(model.fields)):
        result = generate_valid(model)
        key, value = _generate_extra_field_value()

        result[key] = value
        return result

    if not (0 <= target_index < len(model.fields)):
        raise IndexError(
            f"Path index {target_index} out of range for model "
            f"'{model.name}' with {len(model.fields)} fields"
        )

    for i, field in enumerate(model.fields):
        if i != target_index:
            result[field.name] = generate_field(field)
            continue

        if len(task.path) == 1:
            if len(task.allowed_violations) == 0:
                raise ValueError(f"Field '{field.name}' has no constraints to violate")

            value = generate_field(field, task.allowed_violations)

            if value is not _UNSET:
                result[field.name] = value
            continue

        else:
            if field.nested_model is None:
                raise ValueError(f"Field '{field.name}' is not nested model")

            result[field.name] = generate_invalid(
                field.nested_model,
                PlannedTask(
                    path=task.path[1:], allowed_violations=task.allowed_violations
                ),
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

    violation = _choose_violation(violations)

    if violation == ViolationType.TYPE_MISMATCH:
        mismatch_kind = choose_mismatch_kind(field.semantic.kind)
        mismatch_semantic = create_minimal_semantic(mismatch_kind)
        return get_generator(mismatch_kind).generate_value(mismatch_semantic, None)

    if violation == ViolationType.MISSING_FIELD:
        return _UNSET

    return get_generator(field.semantic.kind).generate_value(field.semantic, violation)


def _is_extra_field(task: PlannedTask, target_index: int, len_fields: int) -> bool:
    return (
        len(task.path) == 1
        and target_index == len_fields
        and task.allowed_violations == (ViolationType.EXTRA_FIELD,)
    )


def _choose_violation(
    violations: tuple[ViolationType, ...] | None,
) -> ViolationType | None:
    if violations is None:
        return None

    return random.choice(violations)


def _generate_extra_field_value() -> tuple[str, Any]:
    semantic = create_minimal_semantic(choose_random_base_kind())
    value = get_generator(semantic.kind).generate_value(semantic, None)
    key = "extra"
    return (key, value)
