import math
import sys

import pytest

from conformly.constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
)
from conformly.generator.types.float import (
    FBounds,
    _generate_invalid_float,
    _get_float_valid_borders,
    generate_value,
    supports,
)
from conformly.specs import FieldSpec

# ===== TESTS FOR _get_float_valid_borders_valid_borders() =====


DEFAULT_LOW = -sys.float_info.max
DEFAULT_HIGH = sys.float_info.max


@pytest.mark.parametrize(
    "constraints, expected_low, expected_high",
    [
        # Одиночные ограничения
        pytest.param(
            [GreaterThan(10.0)],
            math.nextafter(10.0, math.inf),
            DEFAULT_HIGH,
            id="single_gt",
        ),
        pytest.param(
            [GreaterOrEqual(18.5)],
            18.5,
            DEFAULT_HIGH,
            id="single_ge",
        ),
        pytest.param(
            [LessThan(66.0)],
            DEFAULT_LOW,
            math.nextafter(66.0, -math.inf),
            id="single_lt",
        ),
        pytest.param(
            [LessOrEqual(100.1)],
            DEFAULT_LOW,
            100.1,
            id="single_le",
        ),
        # Комбинации ограничений
        pytest.param(
            [GreaterThan(10.0), LessThan(66.0)],
            math.nextafter(10.0, math.inf),
            math.nextafter(66.0, -math.inf),
            id="gt_and_lt",
        ),
        pytest.param(
            [GreaterOrEqual(18.5), LessOrEqual(100.0)],
            18.5,
            100.0,
            id="ge_and_le",
        ),
        pytest.param(
            [GreaterThan(10.0), LessOrEqual(66.0)],
            math.nextafter(10.0, math.inf),
            66.0,
            id="gt_and_le",
        ),
        pytest.param(
            [GreaterOrEqual(18.0), LessThan(66.0)],
            18.0,
            math.nextafter(66.0, -math.inf),
            id="ge_and_lt",
        ),
        # Множественные ограничения одного типа
        pytest.param(
            [GreaterThan(5.0), GreaterThan(10.0)],
            math.nextafter(10.0, math.inf),
            DEFAULT_HIGH,
            id="multiple_gt_takes_max",
        ),
        pytest.param(
            [GreaterOrEqual(5.0), GreaterOrEqual(10.0)],
            10.0,
            DEFAULT_HIGH,
            id="multiple_ge_takes_max",
        ),
        pytest.param(
            [LessThan(100.0), LessThan(50.0)],
            DEFAULT_LOW,
            math.nextafter(50.0, -math.inf),
            id="multiple_lt_takes_min",
        ),
        pytest.param(
            [LessOrEqual(100.0), LessOrEqual(50.0)],
            DEFAULT_LOW,
            50.0,
            id="multiple_le_takes_min",
        ),
        # Пограничные случаи
        pytest.param(
            [],
            DEFAULT_LOW,
            DEFAULT_HIGH,
            id="no_constraints",
        ),
        pytest.param(
            [GreaterOrEqual(3.14), LessOrEqual(3.14)],
            3.14,
            3.14,
            id="exact_value_ge_le",
        ),
        pytest.param(
            [
                GreaterThan(5.0),
                GreaterOrEqual(10.0),
                LessThan(100.0),
                LessOrEqual(50.0),
            ],
            10.0,
            50.0,
            id="mixed_constraints",
        ),
    ],
)
def test_get_float_valid_borders(
    constraints: list[Constraint], expected_low: float, expected_high: float
):
    bounds = _get_float_valid_borders(constraints)
    assert bounds.low == pytest.approx(expected_low, abs=1e-15)
    assert bounds.high == pytest.approx(expected_high, abs=1e-15)


@pytest.mark.parametrize(
    "constraints, error_match",
    [
        pytest.param(
            [GreaterThan(100.0), LessThan(50.0)],
            "Min value cannot be higher than max value",
            id="gt_contradicts_lt",
        ),
        pytest.param(
            [GreaterOrEqual(100.0), LessOrEqual(50.0)],
            "Min value cannot be higher than max value",
            id="ge_contradicts_le",
        ),
        pytest.param(
            [GreaterThan(10.0), LessOrEqual(10.0)],
            "Min value cannot be higher than max value",
            id="gt_contradicts_le_same_value",
        ),
        pytest.param(
            [GreaterOrEqual(10.0), LessThan(10.0)],
            "Min value cannot be higher than max value",
            id="ge_contradicts_lt_same_value",
        ),
        pytest.param(
            [GreaterThan(10.0), LessThan(math.nextafter(10.0, math.inf))],
            "Min value cannot be higher than max value",
            id="gt_lt_adjacent_invalid",
        ),
    ],
)
def test_contradictory_float_constraints_raise_error(
    constraints: list[Constraint], error_match: str
):
    with pytest.raises(ValueError, match=error_match):
        _get_float_valid_borders(constraints)


def test_float_extreme_values():
    constraints = [LessOrEqual(sys.float_info.max)]
    bounds = _get_float_valid_borders(constraints)
    assert bounds.low == DEFAULT_LOW
    assert bounds.high == sys.float_info.max

    constraints = [GreaterOrEqual(-sys.float_info.max)]
    bounds = _get_float_valid_borders(constraints)
    assert bounds.low == -sys.float_info.max
    assert bounds.high == DEFAULT_HIGH


def test_contradictory_float_constraints_same_value():
    constraints = [
        GreaterThan(1.0),
        LessThan(1.0),
    ]
    with pytest.raises(ValueError):
        _get_float_valid_borders(constraints)


# ===== TESTS FOR _generate_invalid_float() =====


@pytest.mark.parametrize(
    "bounds",
    [
        pytest.param(FBounds(low=0.0, high=10.0), id="positive"),
        pytest.param(FBounds(low=-10.0, high=0.0), id="negative"),
        pytest.param(FBounds(low=-1.0, high=1.0), id="around_zero"),
        pytest.param(FBounds(low=5.0, high=5.0), id="point"),
        pytest.param(
            FBounds(low=-sys.float_info.max, high=sys.float_info.max), id="full_range"
        ),
    ],
)
def test_generate_invalid_float_always_outside_bounds(bounds: FBounds):
    for _ in range(10):
        invalid_val = _generate_invalid_float(bounds)
        assert invalid_val < bounds.low or invalid_val > bounds.high


# ===== TESTS FOR generate_value() =====


@pytest.mark.parametrize(
    "constraints, valid",
    [
        pytest.param([], True, id="no_constraints_valid"),
        pytest.param([], False, id="no_constraints_invalid"),
        pytest.param([GreaterThan(0)], True, id="gt_valid"),
        pytest.param([GreaterOrEqual(-5.5)], True, id="ge_valid"),
        pytest.param([LessThan(100)], True, id="lt_valid"),
        pytest.param([LessOrEqual(3.14)], True, id="le_valid"),
        pytest.param([GreaterOrEqual(1), LessOrEqual(10)], True, id="range_valid"),
        pytest.param([GreaterThan(0), LessThan(1)], True, id="open_interval_valid"),
        pytest.param([GreaterOrEqual(7), LessOrEqual(7)], True, id="exact_point_valid"),
        # Невалидные значения
        pytest.param([GreaterThan(0)], False, id="gt_invalid"),
        pytest.param([GreaterOrEqual(-5.5)], False, id="ge_invalid"),
        pytest.param([LessThan(100)], False, id="lt_invalid"),
        pytest.param([LessOrEqual(3.14)], False, id="le_invalid"),
        pytest.param([GreaterOrEqual(1), LessOrEqual(10)], False, id="range_invalid"),
        pytest.param([GreaterThan(0), LessThan(1)], False, id="open_interval_invalid"),
        pytest.param(
            [GreaterOrEqual(7), LessOrEqual(7)], False, id="exact_point_invalid"
        ),
    ],
)
def test_generate_value_respects_valid_flag(constraints: list[Constraint], valid: bool):
    bounds = _get_float_valid_borders(constraints)
    low, high = bounds.low, bounds.high

    for _ in range(10):
        value = generate_value(constraints, valid=valid)

        if valid:
            assert low <= value <= high, (
                f"Generated valid value {value} is outside [{low}, {high}]"
            )
        else:
            assert value < low or value > high, (
                f"Generated invalid value {value} is inside [{low}, {high}]"
            )


# ===== TESTS FOR supports() =====


def test_supports_valid():
    assert supports(FieldSpec(name="is", type=float))


@pytest.mark.parametrize("_type", [bool, list, int, dict, str, set])
def test_supports_invalid(_type):
    assert not supports(FieldSpec(name="is", type=_type))
