from ..resolver import ResolvedModel
from ..resolver.semantics import (
    EnumSemantic,
    FieldSemantics,
    NumericSemantic,
    StringSemantic,
)
from ..types import (
    FieldKind,
    FieldPath,
    ViolationType,
)
from .planned_task import PlannedTask


def plan_violation_task(model: ResolvedModel, path: FieldPath) -> PlannedTask:
    field = model.get_field(path)
    return PlannedTask(path, define_allowed_violation_types(field.semantic))


def define_allowed_violation_types(
    semantic: FieldSemantics,
) -> tuple[ViolationType, ...]:
    match semantic:
        case StringSemantic(kind=FieldKind.STRING):
            return define_string_violations(semantic)

        case NumericSemantic(kind=(FieldKind.INTEGER | FieldKind.FLOAT)):
            return define_numeric_violations(semantic)

        case EnumSemantic(kind=FieldKind.ENUM):
            return (ViolationType.NOT_ALLOWED_VALUE,)

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
    valid = semantic.valid_range
    invalid_ranges = semantic.invalid_ranges

    for r in invalid_ranges:
        if r.max_value <= valid.min_value:
            result.append(ViolationType.BELOW_MIN)

        if r.min_value >= valid.max_value:
            result.append(ViolationType.ABOVE_MAX)

    return tuple(result)


def define_string_violations(
    semantic: StringSemantic,
) -> tuple[ViolationType, ...]:
    result: list[ViolationType] = []

    if semantic.length_range.min_length > 0:
        result.append(ViolationType.TOO_SHORT)

    if semantic.length_range.max_length is not None:
        result.append(ViolationType.TOO_LONG)

    if semantic.pattern is not None:
        result.append(ViolationType.PATTERN_MISMATCH)

    return tuple(result)
