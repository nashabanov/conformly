import math
from typing import Any
import uuid

import pytest

from conformly._internal.constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    MultipleOf,
    OneOf,
    Pattern,
)
from conformly._internal.fields import SPECIAL_KINDS, Email
from conformly._internal.parser import ElementSpec, FieldSpec, ModelSpec
from conformly._internal.resolver.resolve import (
    _extract_numeric_multiple_of,
    calculate_invalid_numeric_ranges,
    calculate_max_offset,
    calculate_numeric_bounds,
    create_scalar_semantic,
    create_string_semantic,
    extract_enum_included_values,
)
from conformly._internal.resolver.semantics import (
    BooleanSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly._internal.resolver.semantics.uuid import UUIDSemantic
from conformly._internal.types import (
    FLOAT_MAX,
    FLOAT_MIN,
    INT_MAX,
    INT_MIN,
    FieldKind,
    LengthRange,
    Range,
)
from conformly.exceptions import ResolutionError, SchemaError

# ===== TESTS for create_string_semantic() =====


@pytest.mark.parametrize(
    "constraints, expected",
    [
        (
            (MinLength(5), MaxLength(50), Pattern(r"[a-z]+")),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 50),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (MinLength(3),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(3, None),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MaxLength(100),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 100),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (Pattern(r"[a-z]+"),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (MinLength(5), Pattern(r"[a-z]+")),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (MaxLength(15), Pattern(r"[a-z]+")),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 15),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None),
                pattern=None,
                has_constraints=False,
            ),
        ),
        (
            (MinLength(0),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MaxLength(0),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 0),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MinLength(5), MaxLength(50), Pattern(r"[a-z]+")),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 50),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (MinLength(2), MinLength(5)),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MaxLength(20), MaxLength(10)),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 10),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MinLength(3), MinLength(7), MaxLength(15), MaxLength(10)),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(7, 10),
                pattern=None,
                has_constraints=True,
            ),
        ),
    ],
)
def test_create_string_semantic_valid(
    constraints: tuple[Constraint, ...], expected: StringSemantic
) -> None:
    semantic = create_string_semantic(constraints)
    assert semantic == expected


def test_create_email_kind_string_semantic() -> None:
    semantic = create_string_semantic((), FieldKind.EMAIL)
    assert semantic == StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(0, None),
        pattern=None,
        has_constraints=True,
    )


@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_special_string_kind_raises_with_pattern(kind: FieldKind) -> None:
    with pytest.raises(SchemaError):
        create_string_semantic(constraints=(Pattern(r"\d+"),), field_kind=kind)


@pytest.mark.parametrize("kind", [FieldKind.IPv4, FieldKind.IPv6, FieldKind.IPvAny])
def test_ip_string_kind_raises_with_lengths(kind: FieldKind) -> None:
    with pytest.raises(SchemaError):
        create_string_semantic(constraints=(MinLength(1),), field_kind=kind)

    with pytest.raises(SchemaError):
        create_string_semantic(constraints=(MaxLength(25),), field_kind=kind)


def test_create_string_semantic_ignore_other_constraints() -> None:
    assert create_string_semantic(constraints=(GreaterOrEqual(1),)) == StringSemantic(
        kind=FieldKind.STRING,
        length_range=LengthRange(0, None),
        pattern=None,
        has_constraints=True,
    )


def test_create_string_semantic_invalid_bounds() -> None:
    with pytest.raises(SchemaError):
        create_string_semantic((MinLength(10), MaxLength(3)))


def test_create_string_semantic_double_patten() -> None:
    with pytest.raises(SchemaError):
        create_string_semantic((Pattern(r"\d+"), Pattern(r"[0-9]{3}")))


# ===== TESTS for calculate_numeric_bounds() =====


@pytest.mark.parametrize(
    "field_type, constraints, expected_range",
    [
        (int, (), Range(INT_MIN, INT_MAX)),
        (int, (GreaterOrEqual(5),), Range(5, INT_MAX)),
        (int, (GreaterThan(10),), Range(11, INT_MAX)),
        (int, (LessOrEqual(100),), Range(INT_MIN, 100)),
        (int, (LessThan(20),), Range(INT_MIN, 19)),
        (int, (GreaterOrEqual(10), LessThan(50)), Range(10, 49)),
        (
            int,
            (GreaterThan(5), GreaterOrEqual(10), LessThan(100), LessOrEqual(90)),
            Range(10, 90),
        ),
        (float, (), Range(FLOAT_MIN, FLOAT_MAX)),
        (float, (GreaterOrEqual(2.0),), Range(2.0, FLOAT_MAX)),
        (
            float,
            (GreaterThan(1.5),),
            Range(math.nextafter(1.5, math.inf), FLOAT_MAX),
        ),
        (float, (LessOrEqual(4.2),), Range(FLOAT_MIN, 4.2)),
        (
            float,
            (LessThan(3.7),),
            Range(FLOAT_MIN, math.nextafter(3.7, -math.inf)),
        ),
        (
            float,
            (GreaterOrEqual(1.0), LessThan(2.0)),
            Range(1.0, math.nextafter(2.0, -math.inf)),
        ),
    ],
)
def test_calculate_numeric_bounds_valid(field_type, constraints, expected_range):
    result = calculate_numeric_bounds(field_type, constraints)
    assert result == expected_range


@pytest.mark.parametrize(
    "field_type, constraints",
    [
        (int, (GreaterThan(10), LessThan(5))),
        (int, (GreaterOrEqual(10), LessThan(9))),
        (float, (GreaterThan(5.0), LessThan(3.0))),
        (float, (GreaterOrEqual(2.0), LessThan(1.9))),
    ],
)
def test_calculate_numeric_bounds_invalid_raises(
    field_type: type, constraints: tuple[Constraint, ...]
):
    with pytest.raises(SchemaError):
        calculate_numeric_bounds(field_type, constraints)


@pytest.mark.parametrize("field_type", [int, float])
def test_calculate_numeric_bounds_raises_on_nan(field_type: type) -> None:
    with pytest.raises(SchemaError):
        calculate_numeric_bounds(field_type, (GreaterOrEqual(math.nan),))


# ===== TESTS for calculate_invalid_numeric_ranges =====


@pytest.mark.parametrize(
    "field_type, bounds, expected_ranges",
    [
        (
            int,
            Range(10, 20),
            (
                Range(10 - calculate_max_offset(10, 20), 9),
                Range(21, 20 + calculate_max_offset(10, 20)),
            ),
        ),
        (
            int,
            Range(INT_MIN, 100),
            (Range(101, 100 + calculate_max_offset(INT_MIN, 100)),),
        ),
        (
            int,
            Range(50, INT_MAX),
            (Range(50 - calculate_max_offset(50, INT_MAX), 49),),
        ),
        (
            int,
            Range(INT_MIN, INT_MAX),
            (),
        ),
        (
            int,
            Range(0, 0),
            (
                Range(0 - calculate_max_offset(0, 0), -1),
                Range(1, 0 + calculate_max_offset(0, 0)),
            ),
        ),
        (
            float,
            Range(1.5, 3.7),
            (
                Range(-math.inf, 1.5),
                Range(3.7, math.inf),
            ),
        ),
        (
            float,
            Range(-math.inf, 100.0),
            (Range(100.0, math.inf),),
        ),
        (
            float,
            Range(-5.0, math.inf),
            (Range(-math.inf, -5.0),),
        ),
        (
            float,
            Range(-math.inf, math.inf),
            (),
        ),
        (
            float,
            Range(0.0, 0.0),
            (
                Range(-math.inf, 0.0),
                Range(0.0, math.inf),
            ),
        ),
    ],
)
def test_calculate_invalid_numeric_ranges(field_type, bounds, expected_ranges):
    result = calculate_invalid_numeric_ranges(field_type, bounds)

    assert len(result) == len(expected_ranges)
    for r, exp in zip(result, expected_ranges):
        assert r.min_value == exp.min_value
        assert r.max_value == exp.max_value


def test_unsupported_field_type():
    with pytest.raises(ResolutionError):
        calculate_invalid_numeric_ranges(str, Range(0, 1))


# ===== TESTS for create_string_semantic() =====


@pytest.mark.parametrize(
    "field_type, constraints, nested_model, expected_semantic_type",
    [
        (int, (), None, NumericSemantic),
        (float, (), None, NumericSemantic),
        (str, (), None, StringSemantic),
        (bool, (), None, BooleanSemantic),
        (dict, (), ModelSpec("Inner", "dataclass", ()), ObjectSemantic),
        (Email, (), None, StringSemantic),
        (uuid.UUID, (), None, UUIDSemantic),
    ],
)
def test_create_field_semantic_dispatch(
    field_type: type,
    constraints: tuple[Constraint, ...],
    nested_model: ModelSpec | None,
    expected_semantic_type,
) -> None:
    field_spec = FieldSpec(
        name="test",
        element=ElementSpec(
            field_type=field_type,
            constraints=constraints,
            nested_model=nested_model,
        ),
    )

    semantic = create_scalar_semantic(field_spec.element, field_spec)  # type: ignore
    assert isinstance(semantic, expected_semantic_type)

    if expected_semantic_type is NumericSemantic:
        assert semantic.kind == (
            FieldKind.INTEGER if field_type is int else FieldKind.FLOAT
        )


def test_create_field_semantic_unsupported_type() -> None:
    field_spec = FieldSpec("x", ElementSpec(bytes, ()))
    with pytest.raises(ResolutionError):
        create_scalar_semantic(field_spec.element, field_spec)  # type: ignore


# ===== TESTS for extract_enum_included_values() =====


@pytest.mark.parametrize(
    "constraints, extracted",
    [
        ((OneOf((1, 2, 3)),), (1, 2, 3)),
        ((OneOf(("a", "b", "c")),), ("a", "b", "c")),
        ((OneOf(()),), ()),
    ],
)
def test_extract_enum_included_values_valid(
    constraints: tuple[Constraint], extracted: tuple[Any, ...]
) -> None:
    assert extract_enum_included_values(constraints) == extracted


def test_extract_enum_included_values_more_than_one_constraints() -> None:
    with pytest.raises(SchemaError):
        extract_enum_included_values((OneOf((1, 2)), MaxLength(1)))


def test_extract_enum_included_values_not_one_of() -> None:
    with pytest.raises(SchemaError):
        extract_enum_included_values((MaxLength(1),))


# ===== TESTS for _extract_numeric_multiple_of


@pytest.mark.parametrize(
    "constraints, expected",
    [
        ((MultipleOf(2),), 2),
        ((MultipleOf(2.0), LessOrEqual(10)), 2.0),
        ((LessOrEqual(2.0),), None),
    ],
)
def test_extract_numeric_multiple_of(
    constraints: tuple[Constraint, ...], expected: int | float | None
) -> None:
    assert _extract_numeric_multiple_of(constraints) == expected
