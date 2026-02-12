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
    model: ResolvedModel, path: FieldPath, allow_type_mismatch: bool = False
) -> PlannedTask:
    field = model.get_field(path)
    return PlannedTask(
        path,
        define_allowed_violation_types(
            field.semantic, allow_type_mismatch if not field.nested_model else False
        ),
    )


def define_allowed_violation_types(
    semantic: FieldSemantics, allow_type_mismatch: bool = False
) -> tuple[ViolationType, ...]:
    match semantic:
        case StringSemantic(kind=FieldKind.STRING):
            return define_string_violations(semantic, allow_type_mismatch)

        case NumericSemantic(kind=(FieldKind.INTEGER | FieldKind.FLOAT)):
            return define_numeric_violations(semantic, allow_type_mismatch)

        case EnumSemantic(kind=FieldKind.ENUM):
            if allow_type_mismatch:
                return (ViolationType.NOT_ALLOWED_VALUE, ViolationType.TYPE_MISMATCH)
            return (ViolationType.NOT_ALLOWED_VALUE,)

        case (
            ObjectSemantic(kind=FieldKind.OBJECT)
            | BooleanSemantic(kind=FieldKind.BOOLEAN)
        ):
            if allow_type_mismatch:
                return (ViolationType.TYPE_MISMATCH,)

            raise NotImplementedError(
                f"For {semantic.kind.value} allowed only type mismatch violation"
            )

        case _:
            raise ValueError(f"Unsupported semantic kind: {semantic.kind}")


def define_numeric_violations(
    semantic: NumericSemantic, allow_type_mismatch: bool = False
) -> tuple[ViolationType, ...]:
    result: list[ViolationType] = []
    valid = semantic.valid_range
    invalid_ranges = semantic.invalid_ranges

    for r in invalid_ranges:
        if r.max_value <= valid.min_value:
            result.append(ViolationType.BELOW_MIN)

        if r.min_value >= valid.max_value:
            result.append(ViolationType.ABOVE_MAX)

    if allow_type_mismatch:
        result.append(ViolationType.TYPE_MISMATCH)

    return tuple(result)


def define_string_violations(
    semantic: StringSemantic, allow_type_mismatch: bool = False
) -> tuple[ViolationType, ...]:
    result: list[ViolationType] = []

    if semantic.length_range.min_length > 0:
        result.append(ViolationType.TOO_SHORT)

    if semantic.length_range.max_length is not None:
        result.append(ViolationType.TOO_LONG)

    if semantic.pattern is not None:
        result.append(ViolationType.PATTERN_MISMATCH)

    if allow_type_mismatch:
        result.append(ViolationType.TYPE_MISMATCH)

    return tuple(result)
