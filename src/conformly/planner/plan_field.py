from ..resolver import ResolvedModel
from ..resolver.semantics import (
    BooleanSemantic,
    EnumSemantic,
    FieldSemantics,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from ..types import (
    FieldKind,
    FieldPath,
    ViolationType,
)
from .planned_task import PlannedTask


def plan_violation_task(
    model: ResolvedModel,
    path: FieldPath,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
) -> PlannedTask:
    field = model.get_field(path)
    return PlannedTask(
        path,
        _define_allowed_violation_types(
            semantic=field.semantic,
            allow_type_mismatch=allow_type_mismatch
            if not field.nested_model
            else False,
            allow_structural_violations=allow_structural_violations,
        ),
    )


def _define_allowed_violation_types(
    semantic: FieldSemantics,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
) -> tuple[ViolationType, ...]:
    violations = _define_semantic_violations(semantic)

    if allow_type_mismatch:
        violations.append(ViolationType.TYPE_MISMATCH)

    if allow_structural_violations:
        violations.append(ViolationType.MISSING_FIELD)

    if not violations:
        raise NotImplementedError(
            f"No violations available for {semantic.kind.value} "
            f"(try enabling allow_type_mismatch or allow_structural_violations)"
        )

    return tuple(violations)


def _define_semantic_violations(semantic: FieldSemantics) -> list[ViolationType]:
    match semantic:
        case StringSemantic(kind=FieldKind.STRING):
            return _define_string_violations(semantic)
        case NumericSemantic(kind=(FieldKind.INTEGER | FieldKind.FLOAT)):
            return _define_numeric_violations(semantic)
        case EnumSemantic(kind=FieldKind.ENUM):
            return [ViolationType.NOT_ALLOWED_VALUE]
        case (
            ObjectSemantic(kind=FieldKind.OBJECT)
            | BooleanSemantic(kind=FieldKind.BOOLEAN)
        ):
            return []
        case _:
            raise ValueError(f"Unsupported semantic kind: {semantic.kind}")


def _define_numeric_violations(
    semantic: NumericSemantic,
) -> list[ViolationType]:
    result: list[ViolationType] = []
    valid = semantic.valid_range
    invalid_ranges = semantic.invalid_ranges

    for r in invalid_ranges:
        if r.max_value <= valid.min_value:
            result.append(ViolationType.BELOW_MIN)

        if r.min_value >= valid.max_value:
            result.append(ViolationType.ABOVE_MAX)

    return result


def _define_string_violations(
    semantic: StringSemantic,
) -> list[ViolationType]:
    result: list[ViolationType] = []

    if semantic.length_range.min_length > 0:
        result.append(ViolationType.TOO_SHORT)

    if semantic.length_range.max_length is not None:
        result.append(ViolationType.TOO_LONG)

    if semantic.pattern is not None:
        result.append(ViolationType.PATTERN_MISMATCH)

    return result
