from collections.abc import Callable
from random import choice, randint

from conformly.specs.field import ConstraintSpec


def supports(_type: type) -> bool:
    return _type is int


def generate(constraints: list[ConstraintSpec], valid: bool) -> int:
    low, high = _get_integer_valid_borders(constraints)
    max_offset = max(100, (high - low) * 2)
    if valid:
        return randint(low, high)
    else:
        return _generate_invalid_integer(low, high, max_offset)()


def _generate_invalid_integer(
    low: int, high: int, max_offset: int
) -> Callable[[], int]:
    strategies = {
        "lower": lambda: randint(low - max_offset, low - 1),
        "higher": lambda: randint(high + 1, high + max_offset),
    }
    return lambda: strategies[choice(list(strategies))]()


def _get_integer_valid_borders(constraints: list[ConstraintSpec]) -> tuple[int, int]:
    low = -(2**63)
    high = 2**63 - 1
    for c in constraints:
        v = c.value
        match c.constraint_type:
            case "gt":
                low = max(low, v + 1)
            case "ge":
                low = max(low, v)
            case "lt":
                high = min(high, v - 1)
            case "le":
                high = min(high, v)
    if low > high:
        raise ValueError(
            f"Min value cannot be higher than max value: min: {low}, high {high}"
        )
    return (low, high)
