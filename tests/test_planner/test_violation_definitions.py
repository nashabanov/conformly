from typing import cast

import pytest
from semantic_factories import list_semantic, numeric_semantic, string_semantic

from conformly._internal.planner.field import (
    _define_allowed_violation_types,
    _define_numeric_violations,
    _define_string_violations,
)
from conformly._internal.resolver.semantics import (
    BooleanSemantic,
    EnumSemantic,
    FieldSemantics,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
    UUIDSemantic,
)
from conformly._internal.types import (
    FLOAT_MAX,
    FLOAT_MIN,
    INT_MAX,
    INT_MIN,
    FieldKind,
    LengthRange,
    Range,
    ViolationType,
)
from conformly.exceptions import PlanningError

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


# ===== TESTS for _define_allowed_violation_types() =====


@pytest.mark.parametrize(
    ("allow_type_mismatch", "allow_structural_violations", "prefix"),
    [
        (False, False, ()),
        (True, False, (ViolationType.TYPE_MISMATCH,)),
        (False, True, (ViolationType.MISSING_FIELD,)),
        (
            True,
            True,
            (ViolationType.MISSING_FIELD, ViolationType.TYPE_MISMATCH),
        ),
    ],
)
@pytest.mark.parametrize(
    ("semantic", "semantic_violations"),
    [
        (
            numeric_semantic(),
            (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
        ),
        (
            string_semantic(),
            (
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            EnumSemantic(values=("a", "b", "c"), has_constraints=True),
            (ViolationType.NOT_ALLOWED_VALUE,),
        ),
        (
            list_semantic(string_semantic()),
            (
                ViolationType.TOO_SHORT,
                ViolationType.TOO_LONG,
                ViolationType.PATTERN_MISMATCH,
            ),
        ),
        (
            list_semantic(numeric_semantic()),
            (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
        ),
        (list_semantic(BooleanSemantic()), ()),
        (
            UUIDSemantic(),
            (ViolationType.WRONG_UUID_FORMAT, ViolationType.WRONG_UUID_CHARACTER),
        ),
    ],
)
def test_define_allowed_violations(
    semantic: FieldSemantics,
    semantic_violations: tuple[ViolationType, ...],
    allow_type_mismatch: bool,
    allow_structural_violations: bool,
    prefix: tuple[ViolationType, ...],
) -> None:
    assert _define_allowed_violation_types(
        semantic,
        allow_type_mismatch,
        allow_structural_violations,
    ) == (*prefix, *semantic_violations)


@pytest.mark.parametrize(
    ("allow_type_mismatch", "allow_structural_violations", "expected"),
    [
        (True, False, (ViolationType.TYPE_MISMATCH,)),
        (False, True, (ViolationType.MISSING_FIELD,)),
        (
            True,
            True,
            (ViolationType.MISSING_FIELD, ViolationType.TYPE_MISMATCH),
        ),
    ],
)
@pytest.mark.parametrize("semantic", [BooleanSemantic(), ObjectSemantic()])
def test_define_allowed_non_constraint_violations(
    semantic: FieldSemantics,
    allow_type_mismatch: bool,
    allow_structural_violations: bool,
    expected: tuple[ViolationType, ...],
) -> None:
    assert (
        _define_allowed_violation_types(
            semantic,
            allow_type_mismatch,
            allow_structural_violations,
        )
        == expected
    )


@pytest.mark.parametrize("semantic", [BooleanSemantic(), ObjectSemantic()])
def test_define_allowed_violations_no_sematic_violations(
    semantic: FieldSemantics,
) -> None:
    with pytest.raises(PlanningError):
        _define_allowed_violation_types(semantic)


def test_define_allowed_violations_unsupported_semantic_kind() -> None:
    class UnsupportedSemantic:
        kind = FieldKind.OBJECT

    semantic = cast("FieldSemantics", UnsupportedSemantic())

    with pytest.raises(PlanningError):
        _define_allowed_violation_types(semantic)


def test_list_with_unviolatable_element_returns_empty() -> None:
    semantic = list_semantic(BooleanSemantic())
    assert _define_allowed_violation_types(semantic) == ()
