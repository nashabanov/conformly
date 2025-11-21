import pytest

from conformly.generator.types.integer import _get_integer_valid_borders
from conformly.specs.field import ConstraintSpec

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
    low, high = _get_integer_valid_borders(constraints_list)
    assert low == expected_low
    assert high == expected_high


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
    low, high = _get_integer_valid_borders(constraints)
    assert low == -(2**63)
    assert high == 2**63 - 1

    constraints = [ConstraintSpec(constraint_type="ge", value=-(2**63))]
    low, high = _get_integer_valid_borders(constraints)
    assert low == -(2**63)
    assert high == 2**63 - 1


def test_zero_boundaries():
    constraints = [
        ConstraintSpec(constraint_type="gt", value=-1),
        ConstraintSpec(constraint_type="lt", value=1),
    ]
    low, high = _get_integer_valid_borders(constraints)
    assert low == 0
    assert high == 0
