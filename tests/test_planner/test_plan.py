import pytest

from conformly.planner.plan import (
    define_allowed_violation_types,
    define_numeric_violations,
    define_string_violations,
    plan_violation_task,
)
from conformly.planner.planned_case import PlannedTask
from conformly.resolver import ResolvedField, ResolvedModel
from conformly.resolver.semantics import (
    BooleanSemantic,
    FieldSemantics,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly.types import (
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
            ),
            (ViolationType.PATTERN_MISMATCH,),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING, length_range=LengthRange(5, None), pattern=None
            ),
            (ViolationType.TOO_SHORT,),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING, length_range=LengthRange(0, 10), pattern=None
            ),
            (ViolationType.TOO_LONG,),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING, length_range=LengthRange(5, 15), pattern=None
            ),
            (
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
            ),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING, length_range=LengthRange(5, 15), pattern=r"/\d+/"
            ),
            (
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING, length_range=LengthRange(0, 0), pattern=None
            ),
            (ViolationType.TOO_LONG,),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING, length_range=LengthRange(0, None), pattern=None
            ),
            (),
        ),
    ],
)
def test_define_string_violations(
    semantic: StringSemantic, expected: tuple[ViolationType, ...]
) -> None:
    assert define_string_violations(semantic) == expected


# ===== TESTS for define_numeric_violations() =====


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(2, 10),
                invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
            ),
            (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
        ),
        (
            NumericSemantic(
                kind=FieldKind.FLOAT,
                valid_range=Range(-0.1, FLOAT_MAX),
                invalid_ranges=(Range(FLOAT_MIN, -0.2),),
            ),
            (ViolationType.BELOW_MIN,),
        ),
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(INT_MIN, 120),
                invalid_ranges=(Range(121, INT_MAX),),
            ),
            (ViolationType.ABOVE_MAX,),
        ),
        (
            NumericSemantic(
                kind=FieldKind.FLOAT,
                valid_range=Range(FLOAT_MIN, FLOAT_MAX),
                invalid_ranges=(),
            ),
            (),
        ),
        (
            NumericSemantic(
                kind=FieldKind.FLOAT,
                valid_range=Range(10.1, 11102.3),
                invalid_ranges=(Range(FLOAT_MIN, 10.0), Range(11102.4, FLOAT_MAX)),
            ),
            (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
        ),
    ],
)
def test_define_numeric_violations(
    semantic: NumericSemantic, expected: tuple[ViolationType, ...]
) -> None:
    assert define_numeric_violations(semantic) == expected


# ===== TESTS for define_allowed_violations_types() =====


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (
            NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(2, 10),
                invalid_ranges=(Range(INT_MIN, 1), Range(11, INT_MAX)),
            ),
            (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
        ),
        (
            StringSemantic(
                kind=FieldKind.STRING, length_range=LengthRange(5, 15), pattern=r"/\d+/"
            ),
            (
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
    ],
)
def test_define_allowed_violations_valid(
    semantic: FieldSemantics, expected: tuple[ViolationType, ...]
) -> None:
    assert define_allowed_violation_types(semantic) == expected


@pytest.mark.parametrize(
    "semantic", [BooleanSemantic(FieldKind.BOOLEAN), ObjectSemantic(FieldKind.OBJECT)]
)
def test_define_allowed_violations_invalid(semantic: FieldSemantics) -> None:
    with pytest.raises(NotImplementedError):
        define_allowed_violation_types(semantic)


# ===== TESTS for plan_violation_task() =====


city_field = ResolvedField(
    name="city",
    path=(2, 0, 0),
    py_type=str,
    default=None,
    nullable=False,
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, None), None),
)

zip_field = ResolvedField(
    name="zip",
    path=(2, 0, 1),
    py_type=str,
    default=None,
    nullable=False,
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, 120), None),
)

second_nested = ResolvedModel("Address", (city_field, zip_field))

address_field = ResolvedField(
    name="address",
    path=(2, 0),
    py_type=object,
    default=None,
    nullable=False,
    semantic=ObjectSemantic(FieldKind.OBJECT),
    nested_model=second_nested,
)

phone_field = ResolvedField(
    name="phone",
    path=(2, 1),
    py_type=str,
    default=None,
    nullable=True,
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, 15), None),
)

first_nested = ResolvedModel("Profile", (address_field, phone_field))

name_field = ResolvedField(
    name="name",
    path=(0,),
    py_type=str,
    default=None,
    nullable=False,
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, None), pattern=None),
)

age_field = ResolvedField(
    name="age",
    path=(1,),
    py_type=int,
    default=None,
    nullable=False,
    semantic=NumericSemantic(
        FieldKind.INTEGER, Range(18, 120), (Range(INT_MIN, 17), Range(121, INT_MAX))
    ),
)

profile_field = ResolvedField(
    name="profile",
    path=(2,),
    py_type=object,
    default=None,
    nullable=False,
    semantic=ObjectSemantic(FieldKind.OBJECT),
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
    assert plan_violation_task(base_model, path) == expected


@pytest.mark.parametrize("path", [(3,), (0, 1), (2, 2), (2, 1, 4)])
def test_plan_violation_task_invalid(path: FieldPath) -> None:
    with pytest.raises((IndexError, ValueError)):
        plan_violation_task(base_model, path)
