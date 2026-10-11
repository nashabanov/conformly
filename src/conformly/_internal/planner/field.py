import re

from ._errors import planning_error
from .model import CollectionTarget, PlannedTask

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
    TupleSemantic,
    UUIDSemantic,
)
from conformly._internal.resolver.semantics._domains import finite_cardinality
from conformly._internal.resolver.semantics._numeric import integer_multiple_step
from conformly._internal.resolver.semantics._regex import is_universal_pattern
from conformly._internal.resolver.semantics.dict import DictSemantic
from conformly._internal.types import (
    FieldKind,
    FieldPath,
    ViolationType,
)
from conformly.exceptions import PlanningError

_VIOLATION_PRIORITY: tuple[ViolationType, ...] = (
    # Structural
    ViolationType.MISSING_FIELD,
    ViolationType.EXTRA_FIELD,
    # Type
    ViolationType.TYPE_MISMATCH,
    ViolationType.NONE_FOR_NOT_OPTIONAL,
    # Semantic
    ViolationType.DUPLICATE,
    ViolationType.TOO_LESS_ITEMS,
    ViolationType.TOO_MANY_ITEMS,
    ViolationType.BELOW_MIN,
    ViolationType.ABOVE_MAX,
    ViolationType.NOT_MULTIPLE,
    ViolationType.WRONG_EMAIL_FORMAT,
    ViolationType.WRONG_IP_FORMAT,
    ViolationType.WRONG_URL_FORMAT,
    ViolationType.WRONG_URL_SCHEME,
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

    collection_steps = _plan_collection_steps(model, path)

    if _is_extra_field(model, path):
        if not allow_structural_violations:
            raise planning_error(
                "EXTRA_FIELD requires allow_structural_violations=True",
                code="structural_violtions_not_allowed",
            )
        if forced_violation and forced_violation != ViolationType.EXTRA_FIELD:
            raise planning_error(
                "Extra field only supports EXTRA_FIELD violation",
                code="invalid_forced_violation",
                violation=forced_violation.value,
            )

        return PlannedTask(
            path, (ViolationType.EXTRA_FIELD,), collection_steps=collection_steps
        )

    field = model.get_field(path)

    allowed_violations = _define_allowed_violation_types(
        semantic=field.semantic,
        allow_type_mismatch=allow_type_mismatch if not field.nested_model else False,
        allow_structural_violations=allow_structural_violations,
    )

    if forced_violation is not None:
        if forced_violation not in allowed_violations:
            raise planning_error(
                "Forced violation is not applicable",
                code="invalid_forced_violation",
                violation=forced_violation.value,
                allowed=[v.value for v in allowed_violations],
                field=field.name,
            )
        allowed_violations = (forced_violation,)

    target = (
        _collection_target(field.semantic, allowed_violations[0])
        if allowed_violations
        else None
    )
    return PlannedTask(path, allowed_violations, target, collection_steps)


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

        case ListSemantic(kind=FieldKind.LIST):
            violations = _define_list_violations(semantic)

        case DictSemantic(kind=FieldKind.DICT):
            violations = _define_dict_violations(semantic)

        case TupleSemantic(kind=FieldKind.TUPLE):
            violations = _define_tuple_violations(semantic)

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
                raise planning_error(
                    f"No violations available for {semantic.kind.value}",
                    code="no_violations_availiable",
                    kind=semantic.kind.value,
                    allow_type_mismatch=allow_type_mismatch,
                    allow_structural_violations=allow_structural_violations,
                )

            violations = []

        case _:
            raise planning_error(
                f"Unsupported semantic kind: {semantic.kind.value}",
                code="unsupported_semantic_kind",
                kind=semantic.kind,
            )

    if allow_type_mismatch:
        violations.append(ViolationType.TYPE_MISMATCH)

    if allow_structural_violations:
        violations.append(ViolationType.MISSING_FIELD)

    return tuple(sorted(set(violations), key=_VIOLATION_PRIORITY.index))


def _define_numeric_violations(
    semantic: NumericSemantic,
) -> list[ViolationType]:
    result: list[ViolationType] = []
    valid = semantic.valid_range
    invalid_ranges = semantic.invalid_ranges

    if semantic.multiple_of is not None and (
        semantic.kind != FieldKind.INTEGER
        or integer_multiple_step(semantic.multiple_of) != 1
    ):
        result.append(ViolationType.NOT_MULTIPLE)

    for r in invalid_ranges:
        if r.max_value <= valid.min_value:
            result.append(ViolationType.BELOW_MIN)

        if r.min_value >= valid.max_value:
            result.append(ViolationType.ABOVE_MAX)

    return result


def _pattern_is_universal(pattern: str) -> bool:
    try:
        re.compile(pattern)
        return is_universal_pattern(pattern)
    except re.error as e:
        raise planning_error(
            "Invalid regex pattern", code="invalid_regex_pattern", pattern=pattern
        ) from e


def _define_string_violations(
    semantic: StringSemantic,
) -> list[ViolationType]:
    result: list[ViolationType] = []

    if semantic.kind == FieldKind.EMAIL:
        result.append(ViolationType.WRONG_EMAIL_FORMAT)

    if semantic.kind in (FieldKind.IPv4, FieldKind.IPv6, FieldKind.IPvAny):
        result.append(ViolationType.WRONG_IP_FORMAT)

    if semantic.kind in (FieldKind.HTTPURL, FieldKind.URL):
        result.append(ViolationType.WRONG_URL_SCHEME)

    if semantic.kind == FieldKind.HTTPURL:
        result.append(ViolationType.WRONG_URL_FORMAT)

    if semantic.length_range.min_length > 0:
        result.append(ViolationType.TOO_SHORT)

    if semantic.length_range.max_length is not None:
        result.append(ViolationType.TOO_LONG)

    # Exclude only obvious universal patterns; generation verifies all others.
    if semantic.pattern is not None and not _pattern_is_universal(semantic.pattern):
        result.append(ViolationType.PATTERN_MISMATCH)

    return result


def _has_elements(semantic: ListSemantic | DictSemantic | TupleSemantic) -> bool:
    return semantic.length_range is None or semantic.length_range.max_length != 0


def _define_list_violations(semantic: ListSemantic) -> list[ViolationType]:
    violations: list[ViolationType] = []
    upper = semantic.length_range.max_length if semantic.length_range else None
    if semantic.is_unique_items and (upper is None or upper >= 2):
        violations.append(ViolationType.DUPLICATE)
    if semantic.length_range is not None:
        if semantic.length_range.min_length > 0:
            violations.append(ViolationType.TOO_LESS_ITEMS)
        cardinality = finite_cardinality(semantic.element_semantic)
        if upper is not None and (
            not semantic.is_unique_items or cardinality is None or cardinality > upper
        ):
            violations.append(ViolationType.TOO_MANY_ITEMS)
    if _has_elements(semantic):
        violations.extend(_safe_define(semantic.element_semantic))
    return violations


def _define_dict_violations(semantic: DictSemantic) -> list[ViolationType]:
    violations: list[ViolationType] = []
    if semantic.length_range is not None:
        if semantic.length_range.min_length > 0:
            violations.append(ViolationType.TOO_LESS_ITEMS)
        upper = semantic.length_range.max_length
        cardinality = finite_cardinality(semantic.key_semantic)
        if upper is not None and (cardinality is None or cardinality > upper):
            violations.append(ViolationType.TOO_MANY_ITEMS)
    if _has_elements(semantic):
        violations.extend(_safe_define(semantic.key_semantic))
        violations.extend(_safe_define(semantic.value_semantic))
    return violations


def _safe_define(semantic: FieldSemantics) -> list[ViolationType]:
    try:
        return list(_define_allowed_violation_types(semantic, False, False))
    except PlanningError:
        return []


def _define_tuple_violations(semantic: TupleSemantic) -> list[ViolationType]:
    result: list[ViolationType] = []
    if semantic.is_variadic and semantic.length_range is not None:
        if semantic.length_range.min_length > 0:
            result.append(ViolationType.TOO_LESS_ITEMS)
        if semantic.length_range.max_length is not None:
            result.append(ViolationType.TOO_MANY_ITEMS)
    if not semantic.is_variadic or _has_elements(semantic):
        for item_semantic, _ in semantic.elements_semantics:
            result.extend(_safe_define(item_semantic))
    return result


def _collection_target(
    semantic: FieldSemantics, violation: ViolationType
) -> CollectionTarget | None:
    if violation in (
        ViolationType.DUPLICATE,
        ViolationType.TOO_LESS_ITEMS,
        ViolationType.TOO_MANY_ITEMS,
        ViolationType.MISSING_FIELD,
        ViolationType.TYPE_MISMATCH,
    ):
        return None
    if isinstance(semantic, ListSemantic):
        return CollectionTarget("element")
    if isinstance(semantic, DictSemantic):
        if violation in _safe_define(semantic.key_semantic):
            return CollectionTarget("key")
        return CollectionTarget("value")
    if isinstance(semantic, TupleSemantic):
        for i, (item, _) in enumerate(semantic.elements_semantics):
            if violation in _safe_define(item):
                return CollectionTarget("element", i)
    return None


def _plan_collection_steps(
    model: ResolvedModel, path: FieldPath
) -> tuple[tuple[FieldPath, CollectionTarget], ...]:
    steps: list[tuple[FieldPath, CollectionTarget]] = []
    for depth in range(1, len(path)):
        parent_path = path[:depth]
        parent = model.get_field(parent_path)
        semantic = parent.semantic
        if isinstance(semantic, (ListSemantic, DictSemantic)):
            if not _has_elements(semantic):
                raise planning_error(
                    "Empty-only collection cannot contain the selected target",
                    code="infeasible_collection_target",
                    path=path,
                )
            target = (
                CollectionTarget("element")
                if isinstance(semantic, ListSemantic)
                else CollectionTarget("value")
            )
            steps.append((parent_path, target))
    return tuple(steps)
