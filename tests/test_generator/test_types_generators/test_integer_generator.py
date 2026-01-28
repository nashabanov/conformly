import pytest

from conformly.generator.types.integer import (
    _generate_invalid_integer,
    generate_value,
)
from conformly.resolver.semantics.numeric import NumericSemantic
from conformly.types import INT_MAX, INT_MIN, FieldKind, Range, ViolationType

int_semantic_10_20 = NumericSemantic(
    kind=FieldKind.INTEGER,
    valid_range=Range(10, 20),
    invalid_ranges=(
        Range(-100, 9),
        Range(21, 100),
    ),
    has_constraints=True,
)

int_semantic_ge5 = NumericSemantic(
    kind=FieldKind.INTEGER,
    valid_range=Range(5, INT_MAX),
    invalid_ranges=(Range(-50, 4),),
    has_constraints=True,
)

int_semantic_le100 = NumericSemantic(
    kind=FieldKind.INTEGER,
    valid_range=Range(INT_MIN, 100),
    invalid_ranges=(Range(101, 200),),
    has_constraints=True,
)


# ===== TESTS FOR _generate_invalid_integer() =====


@pytest.mark.parametrize(
    "semantic, violation",
    [
        (int_semantic_10_20, ViolationType.BELOW_MIN),
        (int_semantic_10_20, ViolationType.ABOVE_MAX),
        (int_semantic_ge5, ViolationType.BELOW_MIN),
        (int_semantic_le100, ViolationType.ABOVE_MAX),
    ],
)
def test_generate_invalid_integer(semantic: NumericSemantic, violation: ViolationType):
    for _ in range(30):
        val = _generate_invalid_integer(semantic, violation)
        assert (
            val < semantic.valid_range.min_value or val > semantic.valid_range.max_value
        )
        if violation == ViolationType.BELOW_MIN:
            assert val < semantic.valid_range.min_value

        if violation == ViolationType.ABOVE_MAX:
            assert val > semantic.valid_range.max_value


def test_generate_invalid_integer_no_matching_range_raises():
    semantic = NumericSemantic(
        kind=FieldKind.INTEGER,
        valid_range=Range(0.0, 10.0),
        invalid_ranges=(Range(11.0, 20.0),),
        has_constraints=True,
    )

    with pytest.raises(ValueError):
        _generate_invalid_integer(semantic, ViolationType.BELOW_MIN)


# ===== TESTS FOR generate_value() =====


@pytest.mark.parametrize(
    "semantic, violation",
    [
        (int_semantic_10_20, None),
        (int_semantic_10_20, None),
        (int_semantic_ge5, None),
        (int_semantic_le100, None),
        (int_semantic_10_20, ViolationType.BELOW_MIN),
        (int_semantic_10_20, ViolationType.ABOVE_MAX),
        (int_semantic_ge5, ViolationType.BELOW_MIN),
        (int_semantic_le100, ViolationType.ABOVE_MAX),
    ],
)
def test_generate(semantic: NumericSemantic, violation: ViolationType | None):
    if not violation:
        val = generate_value(semantic, violation)
        assert semantic.valid_range.min_value <= val <= semantic.valid_range.max_value
    else:
        for _ in range(30):
            val = generate_value(semantic, violation)
            assert (
                val < semantic.valid_range.min_value
                or val > semantic.valid_range.max_value
            )
