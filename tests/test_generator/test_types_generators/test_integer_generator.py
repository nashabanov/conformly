import pytest

from conformly.generator.types.integer import (
    Bounds,
    _calculate_max_offset,
    _generate_invalid_integer,
    _get_integer_valid_borders,
    generate_value,
    supports,
)
from conformly.specs import ConstraintSpec, FieldSpec

# ===== TESTS FOR _get_integer_valid_borders() =====


@pytest.mark.parametrize(
    "constraints_list,expected_low,expected_high",
    [
        pytest.param(
            [ConstraintSpec(constraint_type="gt", value=10)],
            11,
            2**63 - 1,
            id="single_gt",
        ),
        pytest.param(
            [ConstraintSpec(constraint_type="ge", value=18)],
            18,
            2**63 - 1,
            id="single_ge",
        ),
        pytest.param(
            [ConstraintSpec(constraint_type="lt", value=66)],
            -(2**63),
            65,
            id="single_lt",
        ),
        pytest.param(
            [ConstraintSpec(constraint_type="le", value=100)],
            -(2**63),
            100,
            id="single_le",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10),
                ConstraintSpec(constraint_type="lt", value=66),
            ],
            11,
            65,
            id="gt_and_lt",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=18),
                ConstraintSpec(constraint_type="le", value=100),
            ],
            18,
            100,
            id="ge_and_le",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10),
                ConstraintSpec(constraint_type="le", value=66),
            ],
            11,
            66,
            id="gt_and_le",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=18),
                ConstraintSpec(constraint_type="lt", value=66),
            ],
            18,
            65,
            id="ge_and_lt",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=5),
                ConstraintSpec(constraint_type="gt", value=10),
            ],
            11,
            2**63 - 1,
            id="multiple_gt_takes_max",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=5),
                ConstraintSpec(constraint_type="ge", value=10),
            ],
            10,
            2**63 - 1,
            id="multiple_ge_takes_max",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="lt", value=100),
                ConstraintSpec(constraint_type="lt", value=50),
            ],
            -(2**63),
            49,
            id="multiple_lt_takes_min",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="le", value=100),
                ConstraintSpec(constraint_type="le", value=50),
            ],
            -(2**63),
            50,
            id="multiple_le_takes_min",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10),
                ConstraintSpec(constraint_type="lt", value=12),
            ],
            11,
            11,
            id="boundaries_touch_valid",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=10),
                ConstraintSpec(constraint_type="le", value=10),
            ],
            10,
            10,
            id="exact_value_ge_le",
        ),
        pytest.param(
            [],
            -(2**63),
            2**63 - 1,
            id="no_constraints",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=5),
                ConstraintSpec(constraint_type="ge", value=10),
                ConstraintSpec(constraint_type="lt", value=100),
                ConstraintSpec(constraint_type="le", value=50),
            ],
            10,
            50,
            id="mixed_constraints",
        ),
    ],
)
def test_get_integer_valid_borders(
    constraints_list: list[ConstraintSpec], expected_low: int, expected_high: int
):
    bounds = _get_integer_valid_borders(constraints_list)
    assert bounds.low == expected_low
    assert bounds.high == expected_high


@pytest.mark.parametrize(
    "constraints,error_match",
    [
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=100),
                ConstraintSpec(constraint_type="lt", value=50),
            ],
            "Min value cannot be higher than max value",
            id="gt_contradicts_lt",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=100),
                ConstraintSpec(constraint_type="le", value=50),
            ],
            "Min value cannot be higher than max value",
            id="ge_contradicts_le",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10),
                ConstraintSpec(constraint_type="le", value=10),
            ],
            "Min value cannot be higher than max value",
            id="gt_contradicts_le_same_value",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="ge", value=10),
                ConstraintSpec(constraint_type="lt", value=10),
            ],
            "Min value cannot be higher than max value",
            id="ge_contradicts_lt_same_value",
        ),
        pytest.param(
            [
                ConstraintSpec(constraint_type="gt", value=10),
                ConstraintSpec(constraint_type="lt", value=11),
            ],
            "Min value cannot be higher than max value",
            id="gt_lt_adjacent_invalid",
        ),
    ],
)
def test_contradictory_constraints_raise_error(
    constraints: list[ConstraintSpec], error_match: str
):
    with pytest.raises(ValueError, match=error_match):
        _get_integer_valid_borders(constraints)


def test_extreme_values():
    constraints = [ConstraintSpec(constraint_type="le", value=2**63 - 1)]
    bounds = _get_integer_valid_borders(constraints)
    assert bounds.low == -(2**63)
    assert bounds.high == 2**63 - 1

    constraints = [ConstraintSpec(constraint_type="ge", value=-(2**63))]
    bounds = _get_integer_valid_borders(constraints)
    assert bounds.low == -(2**63)
    assert bounds.high == 2**63 - 1


def test_zero_boundaries():
    constraints = [
        ConstraintSpec(constraint_type="gt", value=-1),
        ConstraintSpec(constraint_type="lt", value=1),
    ]
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


# ===== TESTS FOR generate() =====


@pytest.mark.parametrize(
    "constraints, valid",
    [
        (
            [
                ConstraintSpec(constraint_type="ge", value=0),
                ConstraintSpec(constraint_type="le", value=10),
            ],
            True,
        ),
        (
            [
                ConstraintSpec(constraint_type="gt", value=5),
                ConstraintSpec(constraint_type="lt", value=15),
            ],
            True,
        ),
        (
            [
                ConstraintSpec(constraint_type="ge", value=0),
                ConstraintSpec(constraint_type="le", value=10),
            ],
            False,
        ),
        (
            [
                ConstraintSpec(constraint_type="gt", value=5),
                ConstraintSpec(constraint_type="lt", value=15),
            ],
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
