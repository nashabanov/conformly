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
    if _is_extra_field(model, path):
        if not allow_structural_violations:
            raise ValueError("EXTRA_FIELD requires allow_structural_violations=True")

        return PlannedTask(path, (ViolationType.EXTRA_FIELD,))

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


def _is_extra_field(model: ResolvedModel, path: FieldPath) -> bool:
    if not path:
        return False

    current_path: tuple[int, ...] = ()
    for _, index in enumerate(path[:-1]):
        current_path = (*current_path, index)

        if current_path not in model.field_map:
            return False

        field = model.field_map[current_path]

        if field.nested_model is None:
            return False

    parent_path = path[:-1]
    if parent_path:
        if parent_path not in model.field_map:
            return False

        parent_field = model.field_map[parent_path]

        if parent_field.nested_model is None:
            return False

        parent_model = parent_field.nested_model
        return path[-1] == len(parent_model.fields)
    else:
        return path[-1] == len(model.fields)


def _define_allowed_violation_types(
    semantic: FieldSemantics,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
) -> tuple[ViolationType, ...]:
    match semantic:
        case StringSemantic(kind=FieldKind.STRING):
            violations = _define_string_violations(semantic)

        case NumericSemantic(kind=(FieldKind.INTEGER | FieldKind.FLOAT)):
            violations = _define_numeric_violations(semantic)

        case EnumSemantic(kind=FieldKind.ENUM):
            violations = [ViolationType.NOT_ALLOWED_VALUE]

        case (
            ObjectSemantic(kind=FieldKind.OBJECT)
            | BooleanSemantic(kind=FieldKind.BOOLEAN)
        ):
            if not (allow_type_mismatch or allow_structural_violations):
                raise NotImplementedError(
                    f"No violations available for {semantic.kind.value} "
                    f"(try enabling allow_type_mismatch or allow_structural_violations)"
                )

            violations = []

        case _:
            raise ValueError(f"Unsupported semantic kind: {semantic.kind}")

    if allow_type_mismatch:
        violations.append(ViolationType.TYPE_MISMATCH)

    if allow_structural_violations:
        violations.append(ViolationType.MISSING_FIELD)

    return tuple(violations)


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
