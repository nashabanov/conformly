import math
import sys

import pytest

from conformly.generator.types.float import (
    FBounds,
    _generate_invalid_float,
    _get_float_valid_borders,
    generate_value,
    supports,
)
from conformly.specs import ConstraintSpec, FieldSpec

# ===== TESTS FOR _get_float_valid_borders_valid_borders() =====


DEFAULT_LOW = -sys.float_info.max
DEFAULT_HIGH = sys.float_info.max


@pytest.mark.parametrize(
    "constraints_list,expected_low,expected_high",
    [
        pytest.param(
            [ConstraintSpec(constraint_type="gt", value=10.0)],
            math.nextafter(10.0, math.inf),
            DEFAULT_HIGH,
            id="single_gt",
        ),
        pytest.param(
            [ConstraintSpec(constraint_type="ge", value=18.5)],
            18.5,
            DEFAULT_HIGH,
            id="single_ge",
        ),
        pytest.param(
            [ConstraintSpec(constraint_type="lt", value=66.0)],
            DEFAULT_LOW,
            math.nextafter(66.0, -math.inf),
            id="single_lt",
        ),
        pytest.param(
            [ConstraintSpec(constraint_type="le", value=100.1)],
            DEFAULT_LOW,
            100.1,
            id="single_le",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10.0),
                ConstraintSpec(constraint_type="lt", value=66.0),
            ],
            math.nextafter(10.0, math.inf),
            math.nextafter(66.0, -math.inf),
            id="gt_and_lt",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=18.5),
                ConstraintSpec(constraint_type="le", value=100.0),
            ],
            18.5,
            100.0,
            id="ge_and_le",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10.0),
                ConstraintSpec(constraint_type="le", value=66.0),
            ],
            math.nextafter(10.0, math.inf),
            66.0,
            id="gt_and_le",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=18.0),
                ConstraintSpec(constraint_type="lt", value=66.0),
            ],
            18.0,
            math.nextafter(66.0, -math.inf),
            id="ge_and_lt",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=5.0),
                ConstraintSpec(constraint_type="gt", value=10.0),
            ],
            math.nextafter(10.0, math.inf),
            DEFAULT_HIGH,
            id="multiple_gt_takes_max",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=5.0),
                ConstraintSpec(constraint_type="ge", value=10.0),
            ],
            10.0,
            DEFAULT_HIGH,
            id="multiple_ge_takes_max",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="lt", value=100.0),
                ConstraintSpec(constraint_type="lt", value=50.0),
            ],
            DEFAULT_LOW,
            math.nextafter(50.0, -math.inf),
            id="multiple_lt_takes_min",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="le", value=100.0),
                ConstraintSpec(constraint_type="le", value=50.0),
            ],
            DEFAULT_LOW,
            50.0,
            id="multiple_le_takes_min",
        ),
        pytest.param(
            [],
            DEFAULT_LOW,
            DEFAULT_HIGH,
            id="no_constraints",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=5.0),
                ConstraintSpec(constraint_type="ge", value=10.0),
                ConstraintSpec(constraint_type="lt", value=100.0),
                ConstraintSpec(constraint_type="le", value=50.0),
            ],
            10.0,
            50.0,
            id="mixed_constraints",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=3.14),
                ConstraintSpec(constraint_type="le", value=3.14),
            ],
            3.14,
            3.14,
            id="exact_value_ge_le",
        ),
    ],
)
def test_get_float_valid_borders(
    constraints_list: list[ConstraintSpec], expected_low: float, expected_high: float
):
    bounds = _get_float_valid_borders(constraints_list)
    assert bounds.low == pytest.approx(expected_low, abs=1e-15)
    assert bounds.high == pytest.approx(expected_high, abs=1e-15)


@pytest.mark.parametrize(
    "constraints,error_match",
    [
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=100.0),
                ConstraintSpec(constraint_type="lt", value=50.0),
            ],
            "Min value cannot be higher than max value",
            id="gt_contradicts_lt",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=100.0),
                ConstraintSpec(constraint_type="le", value=50.0),
            ],
            "Min value cannot be higher than max value",
            id="ge_contradicts_le",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10.0),
                ConstraintSpec(constraint_type="le", value=10.0),
            ],
            "Min value cannot be higher than max value",
            id="gt_contradicts_le_same_value",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=10.0),
                ConstraintSpec(constraint_type="lt", value=10.0),
            ],
            "Min value cannot be higher than max value",
            id="ge_contradicts_lt_same_value",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10.0),
                ConstraintSpec(
                    constraint_type="lt", value=math.nextafter(10.0, math.inf)
                ),
            ],
            "Min value cannot be higher than max value",
            id="gt_lt_adjacent_invalid_due_to_nextafter",
        ),
    ],
)
def test_contradictory_float_constraints_raise_error(
    constraints: list[ConstraintSpec], error_match: str
):
    with pytest.raises(ValueError, match=error_match):
        _get_float_valid_borders(constraints)


def test_float_extreme_values():
    constraints = [ConstraintSpec(constraint_type="le", value=sys.float_info.max)]
    bounds = _get_float_valid_borders(constraints)
    assert bounds.low == DEFAULT_LOW
    assert bounds.high == sys.float_info.max

    constraints = [ConstraintSpec(constraint_type="ge", value=-sys.float_info.max)]
    bounds = _get_float_valid_borders(constraints)
    assert bounds.low == -sys.float_info.max
    assert bounds.high == DEFAULT_HIGH


def test_zero_boundaries_float():
    constraints = [
        ConstraintSpec(constraint_type="gt", value=-1.0),
        ConstraintSpec(constraint_type="lt", value=1.0),
    ]
    bounds = _get_float_valid_borders(constraints)
    expected_low = math.nextafter(-1.0, math.inf)
    expected_high = math.nextafter(1.0, -math.inf)
    assert bounds.low == pytest.approx(expected_low)
    assert bounds.high == pytest.approx(expected_high)


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
        pytest.param([ConstraintSpec("gt", "0")], True, id="gt_valid"),
        pytest.param([ConstraintSpec("ge", "-5.5")], True, id="ge_valid"),
        pytest.param([ConstraintSpec("lt", "100")], True, id="lt_valid"),
        pytest.param([ConstraintSpec("le", "3.14")], True, id="le_valid"),
        pytest.param(
            [ConstraintSpec("ge", "1"), ConstraintSpec("le", "10")],
            True,
            id="range_valid",
        ),
        pytest.param(
            [ConstraintSpec("gt", "0"), ConstraintSpec("lt", "1")],
            True,
            id="open_interval_valid",
        ),
        pytest.param(
            [ConstraintSpec("ge", "7"), ConstraintSpec("le", "7")],
            True,
            id="exact_point_valid",
        ),
        pytest.param([], False, id="no_constraints_invalid"),
        pytest.param([ConstraintSpec("gt", "0")], False, id="gt_invalid"),
        pytest.param([ConstraintSpec("ge", "-5.5")], False, id="ge_invalid"),
        pytest.param([ConstraintSpec("lt", "100")], False, id="lt_invalid"),
        pytest.param([ConstraintSpec("le", "3.14")], False, id="le_invalid"),
        pytest.param(
            [ConstraintSpec("ge", "1"), ConstraintSpec("le", "10")],
            False,
            id="range_invalid",
        ),
        pytest.param(
            [ConstraintSpec("gt", "0"), ConstraintSpec("lt", "1")],
            False,
            id="open_interval_invalid",
        ),
        pytest.param(
            [ConstraintSpec("ge", "7"), ConstraintSpec("le", "7")],
            False,
            id="exact_point_invalid",
        ),
    ],
)
def test_generate_value_respects_valid_flag(
    constraints: list[ConstraintSpec], valid: bool
):
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
