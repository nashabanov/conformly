from typing import Any

from ..planner import PlannedTask
from ..resolver import ResolvedField, ResolvedModel, create_minimal_semantic
from ..types import _UNSET, FieldKind, FieldPath, ViolationType
from .registry import choose_mismatch_kind, get_generator


def generate_valid(model: ResolvedModel) -> dict[str, Any]:
    return {field.name: generate_field(field) for field in model.fields}


def generate_invalid(model: ResolvedModel, task: PlannedTask) -> dict[str, Any]:
    return _built_dict_with_violations(
        model=model,
        target_path=task.path,
        depth=0,
        violations=task.allowed_violations,
    )


def _built_dict_with_violations(
    model: ResolvedModel,
    target_path: FieldPath,
    depth: int,
    violations: tuple[ViolationType, ...],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    target_index = target_path[depth]
    is_leaf = depth == len(target_path) - 1
    fields = model.fields
    total_fields = len(model.fields)

    if target_index < 0 or target_index > total_fields:
        raise IndexError(
            f"Path index {target_index} out of range for model "
            f"'{model.name}' with {total_fields} fields"
        )

    for i in range(0, target_index):
        field = fields[i]
        result[field.name] = generate_field(field)

    if target_index < total_fields:
        field = fields[target_index]

        if is_leaf:
            if len(violations) == 0:
                raise ValueError(f"Field '{field.name}' has no constraints to violate")

            value = generate_field(field, violations)
            if value is not _UNSET:
                result[field.name] = value

        else:
            if field.nested_model is None:
                raise ValueError(f"Field '{field.name}' is not nested model")

            result[field.name] = _built_dict_with_violations(
                model=field.nested_model,
                target_path=target_path,
                depth=depth + 1,
                violations=violations,
            )

    else:
        for i, field in enumerate(fields):
            result[field.name] = generate_field(field)

        key, value = _generate_extra_field_value()
        result[key] = value

    for i in range(target_index + 1, total_fields):
        field = fields[i]
        result[field.name] = generate_field(field)

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


def _choose_violation(
    violations: tuple[ViolationType, ...] | None,
) -> ViolationType | None:
    if violations is None:
        return None

    return violations[0]


def _generate_extra_field_value() -> tuple[str, Any]:
    semantic = create_minimal_semantic(FieldKind.STRING)
    value = get_generator(semantic.kind).generate_value(semantic, None)
    key = "extra"
    return (key, value)
