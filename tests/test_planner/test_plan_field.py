from typing import cast

import pytest

from conformly._internal.parsing import FieldSpec
from conformly.planner.plan_field import (
    _VIOLATION_PRIORITY,
    _define_allowed_violation_types,
    _define_numeric_violations,
    _define_string_violations,
    _is_extra_field,
    plan_violation_task,
)
from conformly.planner.planned_task import PlannedTask
from conformly.resolver import ResolvedField, ResolvedModel
from conformly.resolver.resolve import _build_indexes
from conformly.resolver.semantics import (
    BooleanSemantic,
    EnumSemantic,
    FieldSemantics,
    ListSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly.resolver.semantics.uuid import UUIDSemantic
from conformly.types import (
    _UNSET,
    FLOAT_MAX,
    FLOAT_MIN,
    INT_MAX,
    INT_MIN,
    FieldKind,
    FieldPath,
    LengthRange,
    Range,
    ViolationType,
)

# ===== TESTS for define_string_violations() =====


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None),
                pattern=r"/\d+/",
                has_constraints=True,
            ),
            {ViolationType.PATTERN_MISMATCH},
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None),
                pattern=None,
                has_constraints=True,
            ),
            {ViolationType.TOO_SHORT},
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 10),
                pattern=None,
                has_constraints=True,
            ),
            {ViolationType.TOO_LONG},
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 15),
                pattern=None,
                has_constraints=True,
            ),
            {
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
            },
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 15),
                pattern=r"/\d+/",
                has_constraints=True,
            ),
            {
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            },
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 0),
                pattern=None,
                has_constraints=True,
            ),
            {ViolationType.TOO_LONG},
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None),
                pattern=None,
                has_constraints=False,
            ),
            set(),
        ),
        (
            StringSemantic(
                kind=FieldKind.EMAIL,
                length_range=LengthRange(0, None),
                pattern=None,
                has_constraints=False,
            ),
            {ViolationType.WRONG_EMAIL_FORMAT},
        ),
        (
            StringSemantic(
                kind=FieldKind.EMAIL,
                length_range=LengthRange(5, 65),
                pattern=None,
                has_constraints=False,
            ),
            {
                ViolationType.WRONG_EMAIL_FORMAT,
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
            },
        ),
    ],
)
def test_define_string_violations(
    semantic: StringSemantic, expected: set[ViolationType]
) -> None:
    assert set(_define_string_violations(semantic)) == expected


# ===== TESTS for define_numeric_violations() =====


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(2, 10),
                invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                has_constraints=True,
            ),
            {ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX},
        ),
        (
            NumericSemantic(
                kind=FieldKind.FLOAT,
                valid_range=Range(-0.1, FLOAT_MAX),
                invalid_ranges=(Range(FLOAT_MIN, -0.2),),
                has_constraints=True,
            ),
            {ViolationType.BELOW_MIN},
        ),
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(INT_MIN, 120),
                invalid_ranges=(Range(121, INT_MAX),),
                has_constraints=True,
            ),
            {ViolationType.ABOVE_MAX},
        ),
        (
            NumericSemantic(
                kind=FieldKind.FLOAT,
                valid_range=Range(FLOAT_MIN, FLOAT_MAX),
                invalid_ranges=(),
                has_constraints=False,
            ),
            set(),
        ),
        (
            NumericSemantic(
                kind=FieldKind.FLOAT,
                valid_range=Range(10.1, 11102.3),
                invalid_ranges=(Range(FLOAT_MIN, 10.0), Range(11102.4, FLOAT_MAX)),
                has_constraints=True,
            ),
            {ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX},
        ),
    ],
)
def test_define_numeric_violations(
    semantic: NumericSemantic, expected: set[ViolationType]
) -> None:
    assert set(_define_numeric_violations(semantic)) == expected


# ===== TESTS for _define_allowed_violations_types() =====


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(2, 10),
                invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                has_constraints=True,
            ),
            (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 15),
                pattern=r"/\d+/",
                has_constraints=True,
            ),
            (
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            EnumSemantic(
                values=("a", "b", "c"),
                has_constraints=True,
            ),
            (ViolationType.NOT_ALLOWED_VALUE,),
        ),
        (
            ListSemantic(
                element_semantic=StringSemantic(
                    kind=FieldKind.STRING,
                    length_range=LengthRange(5, 15),
                    pattern=r"/\d+/",
                    has_constraints=True,
                ),
                has_constraints=False,
            ),
            (
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            ListSemantic(
                element_semantic=NumericSemantic(
                    kind=FieldKind.INTEGER,
                    valid_range=Range(2, 10),
                    invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                    has_constraints=True,
                ),
                has_constraints=False,
            ),
            (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
        ),
        (
            ListSemantic(
                element_semantic=BooleanSemantic(has_constraints=False),
                has_constraints=False,
            ),
            (),
        ),
        (
            UUIDSemantic(),
            (ViolationType.WRONG_UUID_FORMAT, ViolationType.WRONG_UUID_CHARACTER),
        ),
    ],
)
def test_define_allowed_violations_valid(
    semantic: FieldSemantics, expected: tuple[ViolationType, ...]
) -> None:
    assert _define_allowed_violation_types(semantic) == expected


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(2, 10),
                invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                has_constraints=True,
            ),
            (
                ViolationType.TYPE_MISMATCH,
                ViolationType.BELOW_MIN,
                ViolationType.ABOVE_MAX,
            ),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 15),
                pattern=r"/\d+/",
                has_constraints=True,
            ),
            (
                ViolationType.TYPE_MISMATCH,
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            EnumSemantic(
                values=("a", "b", "c"),
                has_constraints=True,
            ),
            (ViolationType.TYPE_MISMATCH, ViolationType.NOT_ALLOWED_VALUE),
        ),
        (
            BooleanSemantic(has_constraints=False),
            (ViolationType.TYPE_MISMATCH,),
        ),
        (
            ObjectSemantic(has_constraints=False),
            (ViolationType.TYPE_MISMATCH,),
        ),
        (
            ListSemantic(
                element_semantic=StringSemantic(
                    kind=FieldKind.STRING,
                    length_range=LengthRange(5, 15),
                    pattern=r"/\d+/",
                    has_constraints=True,
                ),
                has_constraints=False,
            ),
            (
                ViolationType.TYPE_MISMATCH,
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            ListSemantic(
                element_semantic=NumericSemantic(
                    kind=FieldKind.INTEGER,
                    valid_range=Range(2, 10),
                    invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                    has_constraints=True,
                ),
                has_constraints=False,
            ),
            (
                ViolationType.TYPE_MISMATCH,
                ViolationType.BELOW_MIN,
                ViolationType.ABOVE_MAX,
            ),
        ),
        (
            ListSemantic(
                element_semantic=BooleanSemantic(has_constraints=False),
                has_constraints=False,
            ),
            (ViolationType.TYPE_MISMATCH,),
        ),
        (
            UUIDSemantic(),
            (
                ViolationType.TYPE_MISMATCH,
                ViolationType.WRONG_UUID_FORMAT,
                ViolationType.WRONG_UUID_CHARACTER,
            ),
        ),
    ],
)
def test_define_allowed_violations_allow_type_mismatch(
    semantic: FieldSemantics, expected: tuple[ViolationType, ...]
) -> None:
    assert _define_allowed_violation_types(semantic, True) == expected


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(2, 10),
                invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                has_constraints=True,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.BELOW_MIN,
                ViolationType.ABOVE_MAX,
            ),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 15),
                pattern=r"/\d+/",
                has_constraints=True,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            EnumSemantic(
                values=("a", "b", "c"),
                has_constraints=True,
            ),
            (ViolationType.MISSING_FIELD, ViolationType.NOT_ALLOWED_VALUE),
        ),
        (
            BooleanSemantic(has_constraints=False),
            (ViolationType.MISSING_FIELD,),
        ),
        (
            ObjectSemantic(has_constraints=False),
            (ViolationType.MISSING_FIELD,),
        ),
        (
            ListSemantic(
                element_semantic=StringSemantic(
                    kind=FieldKind.STRING,
                    length_range=LengthRange(5, 15),
                    pattern=r"/\d+/",
                    has_constraints=True,
                ),
                has_constraints=False,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            ListSemantic(
                element_semantic=NumericSemantic(
                    kind=FieldKind.INTEGER,
                    valid_range=Range(2, 10),
                    invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                    has_constraints=True,
                ),
                has_constraints=False,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.BELOW_MIN,
                ViolationType.ABOVE_MAX,
            ),
        ),
        (
            ListSemantic(
                element_semantic=BooleanSemantic(has_constraints=False),
                has_constraints=False,
            ),
            (ViolationType.MISSING_FIELD,),
        ),
        (
            UUIDSemantic(),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.WRONG_UUID_FORMAT,
                ViolationType.WRONG_UUID_CHARACTER,
            ),
        ),
    ],
)
def test_define_allowed_violations_allow_structural_violations(
    semantic: FieldSemantics, expected: tuple[ViolationType, ...]
) -> None:
    assert _define_allowed_violation_types(semantic, False, True) == expected


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(2, 10),
                invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                has_constraints=True,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TYPE_MISMATCH,
                ViolationType.BELOW_MIN,
                ViolationType.ABOVE_MAX,
            ),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 15),
                pattern=r"/\d+/",
                has_constraints=True,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TYPE_MISMATCH,
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            EnumSemantic(
                values=("a", "b", "c"),
                has_constraints=True,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TYPE_MISMATCH,
                ViolationType.NOT_ALLOWED_VALUE,
            ),
        ),
        (
            BooleanSemantic(has_constraints=False),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TYPE_MISMATCH,
            ),
        ),
        (
            ObjectSemantic(has_constraints=False),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TYPE_MISMATCH,
            ),
        ),
        (
            ListSemantic(
                element_semantic=StringSemantic(
                    kind=FieldKind.STRING,
                    length_range=LengthRange(5, 15),
                    pattern=r"/\d+/",
                    has_constraints=True,
                ),
                has_constraints=False,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TYPE_MISMATCH,
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            ListSemantic(
                element_semantic=NumericSemantic(
                    kind=FieldKind.INTEGER,
                    valid_range=Range(2, 10),
                    invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
                    has_constraints=True,
                ),
                has_constraints=False,
            ),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TYPE_MISMATCH,
                ViolationType.BELOW_MIN,
                ViolationType.ABOVE_MAX,
            ),
        ),
        (
            ListSemantic(
                element_semantic=BooleanSemantic(has_constraints=False),
                has_constraints=False,
            ),
            (ViolationType.MISSING_FIELD, ViolationType.TYPE_MISMATCH),
        ),
        (
            UUIDSemantic(),
            (
                ViolationType.MISSING_FIELD,
                ViolationType.TYPE_MISMATCH,
                ViolationType.WRONG_UUID_FORMAT,
                ViolationType.WRONG_UUID_CHARACTER,
            ),
        ),
    ],
)
def test_define_allowed_violations_all_flags(
    semantic: FieldSemantics, expected: tuple[ViolationType, ...]
) -> None:
    assert _define_allowed_violation_types(semantic, True, True) == expected


@pytest.mark.parametrize("semantic", [BooleanSemantic(), ObjectSemantic()])
def test_define_allowed_violations_no_sematic_violations(
    semantic: FieldSemantics,
) -> None:
    with pytest.raises(NotImplementedError):
        _define_allowed_violation_types(semantic)


def test_define_allowed_violations_unsupported_semantic_kind() -> None:
    class UnsupportedSemantic:
        kind = FieldKind.OBJECT

    semantic = cast("FieldSemantics", UnsupportedSemantic())

    with pytest.raises(ValueError, match="Unsupported semantic kind"):
        _define_allowed_violation_types(semantic)


def test_list_with_unviolatable_element_returns_empty() -> None:
    semantic = ListSemantic(
        element_semantic=BooleanSemantic(has_constraints=False),
        has_constraints=False,
    )
    assert _define_allowed_violation_types(semantic) == ()


# ===== TESTS for plan_violation_task() =====


city_field = ResolvedField(
    field_spec=FieldSpec(name="city", field_type=str, default=_UNSET, nullable=False),
    path=(2, 0, 0),
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, None), None, False),
)

zip_field = ResolvedField(
    field_spec=FieldSpec(name="zip", field_type=str, default=_UNSET, nullable=False),
    path=(2, 0, 1),
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, 120), None, True),
)

second_nested = ResolvedModel("Address", (city_field, zip_field))

address_field = ResolvedField(
    field_spec=FieldSpec(
        name="address", field_type=object, default=_UNSET, nullable=False
    ),
    path=(2, 0),
    semantic=ObjectSemantic(False),
    nested_model=second_nested,
)

phone_field = ResolvedField(
    field_spec=FieldSpec(name="phone", field_type=str, default=_UNSET, nullable=True),
    path=(2, 1),
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, 15), None, False),
)

first_nested = ResolvedModel("Profile", (address_field, phone_field))

name_field = ResolvedField(
    field_spec=FieldSpec(name="name", field_type=str, default=_UNSET, nullable=False),
    path=(0,),
    semantic=StringSemantic(
        FieldKind.STRING, LengthRange(0, None), pattern=None, has_constraints=True
    ),
)

age_field = ResolvedField(
    field_spec=FieldSpec(name="age", field_type=int, default=_UNSET, nullable=False),
    path=(1,),
    semantic=NumericSemantic(
        FieldKind.INTEGER,
        Range(18, 120),
        (Range(INT_MIN, 17), Range(121, INT_MAX)),
        True,
    ),
)

profile_field = ResolvedField(
    field_spec=FieldSpec(
        name="profile", field_type=object, default=_UNSET, nullable=False
    ),
    path=(2,),
    semantic=ObjectSemantic(False),
    nested_model=first_nested,
)

base_model = ResolvedModel("User", (name_field, age_field, profile_field))


@pytest.mark.parametrize(
    "path, expected",
    [
        ((0,), PlannedTask((0,), ())),
        ((1,), PlannedTask((1,), (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX))),
        ((2, 1), PlannedTask((2, 1), (ViolationType.TOO_LONG,))),
        ((2, 0, 0), PlannedTask((2, 0, 0), ())),
    ],
)
def test_plan_violation_task_valid(path: FieldPath, expected: PlannedTask) -> None:
    _build_indexes(base_model)
    assert plan_violation_task(base_model, path) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        ((0,), PlannedTask((0,), (ViolationType.TYPE_MISMATCH,))),
        (
            (1,),
            PlannedTask(
                (1,),
                (
                    ViolationType.TYPE_MISMATCH,
                    ViolationType.BELOW_MIN,
                    ViolationType.ABOVE_MAX,
                ),
            ),
        ),
        (
            (2, 1),
            PlannedTask(
                (2, 1),
                (
                    ViolationType.TYPE_MISMATCH,
                    ViolationType.TOO_LONG,
                ),
            ),
        ),
        ((2, 0, 0), PlannedTask((2, 0, 0), (ViolationType.TYPE_MISMATCH,))),
    ],
)
def test_plan_violation_task_allow_type_mismatch(
    path: FieldPath, expected: PlannedTask
) -> None:
    _build_indexes(base_model)
    assert plan_violation_task(base_model, path, True) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        ((0,), PlannedTask((0,), (ViolationType.MISSING_FIELD,))),
        (
            (1,),
            PlannedTask(
                (1,),
                (
                    ViolationType.MISSING_FIELD,
                    ViolationType.BELOW_MIN,
                    ViolationType.ABOVE_MAX,
                ),
            ),
        ),
        (
            (2, 1),
            PlannedTask(
                (2, 1),
                (
                    ViolationType.MISSING_FIELD,
                    ViolationType.TOO_LONG,
                ),
            ),
        ),
        ((2, 0, 0), PlannedTask((2, 0, 0), (ViolationType.MISSING_FIELD,))),
    ],
)
def test_plan_violation_task_allow_structural_violations(
    path: FieldPath, expected: PlannedTask
) -> None:
    _build_indexes(base_model)
    assert plan_violation_task(base_model, path, False, True) == expected


@pytest.mark.parametrize(
    "path",
    [(3,), (2, 2), (2, 0, 2)],
)
def test_plan_violation_task_valid_extra_field(path: FieldPath) -> None:
    _build_indexes(base_model)
    assert plan_violation_task(base_model, path, False, True) == PlannedTask(
        path, (ViolationType.EXTRA_FIELD,)
    )


@pytest.mark.parametrize("path", [(3,), (0, 1), (2, 2), (2, 1, 4)])
def test_plan_violation_task_invalid(path: FieldPath) -> None:
    with pytest.raises((IndexError, ValueError)):
        plan_violation_task(base_model, path)


def test_plan_violation_task_raises_for_type_mismatch_nested_models() -> None:
    with pytest.raises(NotImplementedError):
        plan_violation_task(base_model, (2,), True)


@pytest.mark.parametrize("path", [(5,), (2, 5), (2, 0, 4)])
def test_plan_violation_task_invalid_extra_field(path: FieldPath) -> None:
    with pytest.raises((IndexError, ValueError)):
        plan_violation_task(base_model, path, False, True)


# ===== TESTS for _is_extra_field() =====


def test_is_extra_field_no_path() -> None:
    assert not _is_extra_field(base_model, ())


def test_is_extra_field_path_longer_than_extra() -> None:
    assert not _is_extra_field(base_model, (4,))


def test_is_extra_field_path_longer_than_extra_nester() -> None:
    assert not _is_extra_field(base_model, (2, 5))


# ===== TESTS for violation priority =====


def test_all_violation_types_in_priority() -> None:
    priority_set = set(_VIOLATION_PRIORITY)
    all_violations = set(ViolationType)

    missing = all_violations - priority_set
    assert not missing, f"ViolationType(s) not in _VIOLATION_PRIORITY: {missing}"


def test_first_violation_is_highest_priority() -> None:
    _build_indexes(base_model)

    test_cases = [
        ((0,), True, True, ViolationType.MISSING_FIELD),
        ((1,), True, True, ViolationType.MISSING_FIELD),
        ((2, 1), True, True, ViolationType.MISSING_FIELD),
    ]

    for path, allow_type, allow_struct, expected_first in test_cases:
        task = plan_violation_task(
            base_model,
            path,
            allow_type_mismatch=allow_type,
            allow_structural_violations=allow_struct,
        )
        assert task.allowed_violations[0] == expected_first, (
            f"Field {path}: expected {expected_first}, got {task.allowed_violations[0]}"
        )


def test_violations_sorted_by_priority() -> None:
    _build_indexes(base_model)

    task = plan_violation_task(
        base_model,
        path=(1,),
        allow_type_mismatch=True,
        allow_structural_violations=True,
    )

    expected = (
        ViolationType.MISSING_FIELD,
        ViolationType.TYPE_MISMATCH,
        ViolationType.BELOW_MIN,
        ViolationType.ABOVE_MAX,
    )

    assert task.allowed_violations == expected
