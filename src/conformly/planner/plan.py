from ..resolver import ResolvedField, ResolvedModel
from ..resolver.semantics import NumericSemantic, StringSemantic
from ..types import (
    FieldKind,
    FieldPath,
    ViolationType,
)
from .planned_case import PlannedTask


def plan_violation_task(model: ResolvedModel, path: FieldPath) -> PlannedTask:
    field = find_resolved_field(model, path)
    return PlannedTask(path, define_allowed_violation_types(field))


def find_resolved_field(model: ResolvedModel, path: FieldPath) -> ResolvedField: ...


def define_allowed_violation_types(
    field: ResolvedField,
) -> tuple[ViolationType, ...]:
    semantic = field.semantic

    match semantic:
        case StringSemantic(kind=FieldKind.STRING):
            return define_string_violations(semantic)

        case NumericSemantic(kind=(FieldKind.INTEGER | FieldKind.FLOAT)):
            return define_numeric_violations(semantic)

        case _ if semantic.kind in (FieldKind.OBJECT, FieldKind.BOOLEAN):
            raise NotImplementedError(
                f"There is no violations for {semantic.kind.value} fields yet"
            )

        case _:
            raise ValueError(f"Unsupported semantic kind: {semantic.kind}")


def define_numeric_violations(
    semantic: NumericSemantic,
) -> tuple[ViolationType, ...]:
    result: list[ViolationType] = []

    return tuple(result)


def define_string_violations(
    semantic: StringSemantic,
) -> tuple[ViolationType, ...]:
    result: list[ViolationType] = []

    if semantic.pattern is not None:
        result.append(ViolationType.PATTERN_MISMATCH)

    if semantic.length_range.max_length is not None:
        result.append(ViolationType.TOO_LONG)

    if semantic.length_range.min_length > 0:
        result.append(ViolationType.TOO_SHORT)

    return tuple(result)
