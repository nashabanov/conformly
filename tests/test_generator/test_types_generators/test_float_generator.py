import math

import pytest

from conformly.generator.types.float import (
    _generate_invalid_float,
    generate_value,
)
from conformly.resolver.semantics import NumericSemantic
from conformly.types import FLOAT_MAX, FLOAT_MIN, FieldKind, Range, ViolationType

valid_range_10_20 = Range(10.0, 20.0)

invalid_ranges_10_20 = (
    Range(FLOAT_MIN, 9.9),
    Range(20.1, FLOAT_MAX),
)

semantic_10_20 = NumericSemantic(
    kind=FieldKind.FLOAT,
    valid_range=valid_range_10_20,
    invalid_ranges=invalid_ranges_10_20,
)


# ===== TESTS FOR _generate_invalid_float() =====


@pytest.mark.parametrize(
    "semantic, violation",
    [
        (semantic_10_20, ViolationType.BELOW_MIN),
        (semantic_10_20, ViolationType.ABOVE_MAX),
    ],
)
def test_generate_invalid_float_always_outside_bounds(
    semantic: NumericSemantic, violation: ViolationType
):
    valid_range = semantic.valid_range
    for _ in range(10):
        invalid_val = _generate_invalid_float(semantic, violation)
        assert (
            invalid_val < valid_range.min_value or invalid_val > valid_range.max_value
        )
        if violation == ViolationType.ABOVE_MAX:
            assert invalid_val > valid_range.max_value

        if violation == ViolationType.BELOW_MIN:
            assert invalid_val < valid_range.min_value


def test_generate_invalid_float_no_matching_range_raises():
    semantic_no_below = NumericSemantic(
        kind=FieldKind.FLOAT,
        valid_range=Range(0.0, 1.0),
        invalid_ranges=(Range(2.0, 3.0),),
    )

    with pytest.raises(ValueError, match="No invalid ranges available for violation"):
        _generate_invalid_float(semantic_no_below, ViolationType.BELOW_MIN)


# ===== TESTS FOR generate_value() =====


bounded_semantic = NumericSemantic(
    kind=FieldKind.FLOAT,
    valid_range=Range(10.0, 20.0),
    invalid_ranges=(Range(-100.0, 9.9), Range(20.1, 100.0)),
)

upper_bounded_semantic = NumericSemantic(
    kind=FieldKind.FLOAT,
    valid_range=Range(FLOAT_MIN, 5.0),
    invalid_ranges=(Range(5.1, 100.0),),
)

lower_bounded_semantic = NumericSemantic(
    kind=FieldKind.FLOAT,
    valid_range=Range(-3.0, FLOAT_MAX),
    invalid_ranges=(Range(-100.0, -3.1),),
)

unbounded_semantic = NumericSemantic(
    kind=FieldKind.FLOAT,
    valid_range=Range(FLOAT_MIN, FLOAT_MAX),
    invalid_ranges=(),
)


@pytest.mark.parametrize(
    "semantic, violation",
    [
        (bounded_semantic, None),
        (upper_bounded_semantic, None),
        (lower_bounded_semantic, None),
        (unbounded_semantic, None),
        (bounded_semantic, ViolationType.BELOW_MIN),
        (bounded_semantic, ViolationType.ABOVE_MAX),
        (upper_bounded_semantic, ViolationType.ABOVE_MAX),
        (lower_bounded_semantic, ViolationType.BELOW_MIN),
    ],
)
def test_generate_value_respects_valid_flag(
    semantic: NumericSemantic, violation: ViolationType | None
):
    valid_range = semantic.valid_range
    min, max = valid_range.min_value, valid_range.max_value

    for _ in range(10):
        value = generate_value(semantic, violation)

        if not violation:
            assert min <= value <= max, (
                f"Generated valid value {value} is outside [{min}, {max}]"
            )
        else:
            assert value < min or value > max, (
                f"Generated invalid value {value} is inside [{min}, {max}]"
            )


def test_generate_value_invalid_on_unbounded_raises():
    with pytest.raises(ValueError, match="No invalid ranges available"):
        generate_value(unbounded_semantic, ViolationType.BELOW_MIN)


def test_generate_value_unbounded_uses_safe_range():
    semantic = unbounded_semantic
    values = [generate_value(semantic, None) for _ in range(100)]
    for v in values:
        assert -1e300 <= v <= 1e300
        assert math.isfinite(v)
