from .model import PlannedTask

from conformly._internal.fields import SPECIAL_KINDS
from conformly._internal.resolver import ResolvedModel
from conformly._internal.resolver.semantics import (
    BooleanSemantic,
    EnumSemantic,
    FieldSemantics,
    ListSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
    UUIDSemantic,
)
from conformly._internal.types import (
    FieldKind,
    FieldPath,
    ViolationType,
)

_VIOLATION_PRIORITY: tuple[ViolationType, ...] = (
    # Structural
    ViolationType.MISSING_FIELD,
    ViolationType.EXTRA_FIELD,
    # Type
    ViolationType.TYPE_MISMATCH,
    ViolationType.NONE_FOR_NOT_OPTIONAL,
    # Semantic
    ViolationType.BELOW_MIN,
    ViolationType.ABOVE_MAX,
    ViolationType.NOT_MULTIPLE,
    ViolationType.WRONG_EMAIL_FORMAT,
    ViolationType.WRONG_IP_FORMAT,
    ViolationType.WRONG_UUID_FORMAT,
    ViolationType.WRONG_UUID_CHARACTER,
    ViolationType.TOO_SHORT,
    ViolationType.TOO_LONG,
    ViolationType.PATTERN_MISMATCH,
    ViolationType.NOT_ALLOWED_VALUE,
)


def plan_violation_task(
    model: ResolvedModel,
    path: FieldPath,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
    forced_violation: ViolationType | None = None,
) -> PlannedTask:
    if forced_violation:
        if forced_violation in (ViolationType.EXTRA_FIELD, ViolationType.MISSING_FIELD):
            allow_structural_violations = True
        if forced_violation == ViolationType.TYPE_MISMATCH:
            allow_type_mismatch = True

    if _is_extra_field(model, path):
        if not allow_structural_violations:
            raise ValueError("EXTRA_FIELD requires allow_structural_violations=True")
        if forced_violation and forced_violation != ViolationType.EXTRA_FIELD:
            raise ValueError(
                f"Extra field only supports EXTRA_FIELD violation, "
                f"got {forced_violation.value}"
            )

        return PlannedTask(path, (ViolationType.EXTRA_FIELD,))

    field = model.get_field(path)

    allowed_violations = _define_allowed_violation_types(
        semantic=field.semantic,
        allow_type_mismatch=allow_type_mismatch if not field.nested_model else False,
        allow_structural_violations=allow_structural_violations,
    )

    if forced_violation is not None:
        if forced_violation not in allowed_violations:
            raise ValueError(
                f"Violation type '{forced_violation.value}' is not applicable "
                f"to field '{field.name}' (kind: {field.semantic.kind.value}). "
                f"Available for this field: {[v.value for v in allowed_violations]}"
            )
        return PlannedTask(path, (forced_violation,))

    return PlannedTask(path, allowed_violations)


def _is_extra_field(model: ResolvedModel, path: FieldPath) -> bool:
    if not path:
        return False

    return path in model.extra_paths


def _define_allowed_violation_types(
    semantic: FieldSemantics,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
) -> tuple[ViolationType, ...]:
    match semantic:
        case StringSemantic(kind=kind) if kind in SPECIAL_KINDS | {FieldKind.STRING}:
            violations = _define_string_violations(semantic)

        case NumericSemantic(kind=(FieldKind.INTEGER | FieldKind.FLOAT)):
            violations = _define_numeric_violations(semantic)

        case ListSemantic(element_semantic=elem_sem):
            try:
                violations = list(
                    _define_allowed_violation_types(elem_sem, False, False)
                )
            except NotImplementedError:
                violations = []

        case EnumSemantic(kind=FieldKind.ENUM):
            violations = [ViolationType.NOT_ALLOWED_VALUE]

        case UUIDSemantic(kind=FieldKind.UUID):
            violations = [
                ViolationType.WRONG_UUID_FORMAT,
                ViolationType.WRONG_UUID_CHARACTER,
            ]

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

    violations.sort(key=lambda v: _VIOLATION_PRIORITY.index(v))

    return tuple(violations)


def _define_numeric_violations(
    semantic: NumericSemantic,
) -> list[ViolationType]:
    result: list[ViolationType] = []
    valid = semantic.valid_range
    invalid_ranges = semantic.invalid_ranges

    if semantic.multiple_of is not None:
        result.append(ViolationType.NOT_MULTIPLE)

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

    if semantic.kind == FieldKind.EMAIL:
        result.append(ViolationType.WRONG_EMAIL_FORMAT)

    if semantic.kind in (FieldKind.IPv4, FieldKind.IPv6, FieldKind.IPvAny):
        result.append(ViolationType.WRONG_IP_FORMAT)

    if semantic.length_range.min_length > 0:
        result.append(ViolationType.TOO_SHORT)

    if semantic.length_range.max_length is not None:
        result.append(ViolationType.TOO_LONG)

    if semantic.pattern is not None:
        result.append(ViolationType.PATTERN_MISMATCH)

    return result
