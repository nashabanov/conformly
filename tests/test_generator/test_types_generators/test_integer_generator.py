from collections.abc import Sequence

import pytest

from conformly.constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
)
from conformly.generator.types.integer import (
    Bounds,
    _calculate_max_offset,
    _generate_invalid_integer,
    _get_integer_valid_borders,
    generate_value,
    supports,
)
from conformly.specs import FieldSpec

DEFAULT_LOW = -(2**63)
DEFAULT_HIGH = 2**63 - 1


# ===== TESTS FOR _get_integer_valid_borders() =====


@pytest.mark.parametrize(
    "constraints, expected_low, expected_high",
    [
        # Одиночные ограничения
        pytest.param(
            [GreaterThan(10)],
            11,
            DEFAULT_HIGH,
            id="single_gt",
        ),
        pytest.param(
            [GreaterOrEqual(18)],
            18,
            DEFAULT_HIGH,
            id="single_ge",
        ),
        pytest.param(
            [LessThan(66)],
            DEFAULT_LOW,
            65,
            id="single_lt",
        ),
        pytest.param(
            [LessOrEqual(100)],
            DEFAULT_LOW,
            100,
            id="single_le",
        ),
        # Комбинации ограничений
        pytest.param(
            [GreaterThan(10), LessThan(66)],
            11,
            65,
            id="gt_and_lt",
        ),
        pytest.param(
            [GreaterOrEqual(18), LessOrEqual(100)],
            18,
            100,
            id="ge_and_le",
        ),
        pytest.param(
            [GreaterThan(10), LessOrEqual(66)],
            11,
            66,
            id="gt_and_le",
        ),
        pytest.param(
            [GreaterOrEqual(18), LessThan(66)],
            18,
            65,
            id="ge_and_lt",
        ),
        # Множественные ограничения одного типа
        pytest.param(
            [GreaterThan(5), GreaterThan(10)],
            11,
            DEFAULT_HIGH,
            id="multiple_gt_takes_max",
        ),
        pytest.param(
            [GreaterOrEqual(5), GreaterOrEqual(10)],
            10,
            DEFAULT_HIGH,
            id="multiple_ge_takes_max",
        ),
        pytest.param(
            [LessThan(100), LessThan(50)],
            DEFAULT_LOW,
            49,
            id="multiple_lt_takes_min",
        ),
        pytest.param(
            [LessOrEqual(100), LessOrEqual(50)],
            DEFAULT_LOW,
            50,
            id="multiple_le_takes_min",
        ),
        # Пограничные случаи
        pytest.param(
            [GreaterThan(10), LessThan(12)],
            11,
            11,
            id="boundaries_touch_valid",
        ),
        pytest.param(
            [GreaterOrEqual(10), LessOrEqual(10)],
            10,
            10,
            id="exact_value_ge_le",
        ),
        pytest.param(
            [],
            DEFAULT_LOW,
            DEFAULT_HIGH,
            id="no_constraints",
        ),
        pytest.param(
            [
                GreaterThan(5),
                GreaterOrEqual(10),
                LessThan(100),
                LessOrEqual(50),
            ],
            10,
            50,
            id="mixed_constraints",
        ),
    ],
)
def test_get_integer_valid_borders(
    constraints: Sequence[Constraint], expected_low: int, expected_high: int
):
    bounds = _get_integer_valid_borders(constraints)
    assert bounds.low == expected_low
    assert bounds.high == expected_high


@pytest.mark.parametrize(
    "constraints, error_match",
    [
        pytest.param(
            [GreaterThan(100), LessThan(50)],
            "Min value cannot be higher than max value",
            id="gt_contradicts_lt",
        ),
        pytest.param(
            [GreaterOrEqual(100), LessOrEqual(50)],
            "Min value cannot be higher than max value",
            id="ge_contradicts_le",
        ),
        pytest.param(
            [GreaterThan(10), LessOrEqual(10)],
            "Min value cannot be higher than max value",
            id="gt_contradicts_le_same_value",
        ),
        pytest.param(
            [GreaterOrEqual(10), LessThan(10)],
            "Min value cannot be higher than max value",
            id="ge_contradicts_lt_same_value",
        ),
        pytest.param(
            [GreaterThan(10), LessThan(11)],
            "Min value cannot be higher than max value",
            id="gt_lt_adjacent_invalid",
        ),
    ],
)
def test_contradictory_constraints_raise_error(
    constraints: Sequence[Constraint], error_match: str
):
    with pytest.raises(ValueError, match=error_match):
        _get_integer_valid_borders(constraints)


def test_extreme_values():
    constraints = [LessOrEqual(2**63 - 1)]
    bounds = _get_integer_valid_borders(constraints)
    assert bounds.low == -(2**63)
    assert bounds.high == 2**63 - 1

    constraints = [GreaterOrEqual(-(2**63))]
    bounds = _get_integer_valid_borders(constraints)
    assert bounds.low == -(2**63)
    assert bounds.high == 2**63 - 1


def test_zero_boundaries():
    constraints = [GreaterThan(-1), LessThan(1)]
    bounds = _get_integer_valid_borders(constraints)
    assert bounds.low == 0
    assert bounds.high == 0


# ===== TESTS FOR _calculate_max_offset() =====


@pytest.mark.parametrize(
    "bounds,expected_result",
    [
        pytest.param(Bounds(0, 10), 100),
        pytest.param(Bounds(5, 5), 100),
        pytest.param(Bounds(0, 600000), 1000000),
        pytest.param(Bounds(-100, -50), 100),
        pytest.param(Bounds(-50000, 40000), 180000),
    ],
)
def test_calculate_max_offset(bounds, expected_result):
    assert _calculate_max_offset(bounds) == expected_result


# ===== TESTS FOR _generate_invalid_integer() =====


@pytest.mark.parametrize(
    "bounds",
    [
        pytest.param(Bounds(0, 10)),
        pytest.param(Bounds(5, 5)),
        pytest.param(Bounds(-100, -50)),
        pytest.param(Bounds(1000, 5000)),
        pytest.param(Bounds(-50000, 40000)),
    ],
)
def test_generate_invalid_integer(bounds):
    max_offset = _calculate_max_offset(bounds)
    for _ in range(30):  # Проверяем на нескольких итерациях для вероятностной проверки
        val = _generate_invalid_integer(bounds)
        assert val < bounds.low or val > bounds.high, (
            f"Value {val} should be outside [{bounds.low}, {bounds.high}]"
        )
        if val < bounds.low:
            assert bounds.low - max_offset <= val <= bounds.low - 1, (
                f"Value {val} out of lower expected range"
            )
        else:
            assert bounds.high + 1 <= val <= bounds.high + max_offset, (
                f"Value {val} out of higher expected range"
            )


# ===== TESTS FOR generate_value() =====


@pytest.mark.parametrize(
    "constraints, valid",
    [
        (
            [GreaterOrEqual(0), LessOrEqual(10)],
            True,
        ),
        (
            [GreaterThan(5), LessThan(15)],
            True,
        ),
        (
            [GreaterOrEqual(0), LessOrEqual(10)],
            False,
        ),
        (
            [GreaterThan(5), LessThan(15)],
            False,
        ),
    ],
)
def test_generate(constraints, valid):
    bounds = _get_integer_valid_borders(constraints)

    if valid:
        val = generate_value(constraints, valid)
        assert bounds.low <= val <= bounds.high
    else:
        for _ in range(30):
            val = generate_value(constraints, valid)
            assert val < bounds.low or val > bounds.high


# ===== TESTS_FOR_supports() =====


def test_supports_valid():
    assert supports(FieldSpec(name="is", type=int))


@pytest.mark.parametrize("_type", [bool, list, float, dict, str, set])
def test_supports_invalid(_type):
    assert not supports(FieldSpec(name="is", type=_type))
