from __future__ import annotations

from dataclasses import dataclass
from random import choice, randint
from typing import TYPE_CHECKING

from conformly.constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from conformly.specs import FieldSpec


def supports(field: FieldSpec) -> bool:
    return field.type is int


@dataclass(frozen=True)
class Bounds:
    low: int
    high: int
    has_low: bool
    has_high: bool


def generate_value(constraints: Sequence[Constraint], valid: bool) -> int:
    bounds = _get_integer_valid_borders(constraints)
    if valid:
        return randint(bounds.low, bounds.high)
    else:
        return _generate_invalid_integer(bounds)


def _generate_invalid_integer(bounds: Bounds) -> int:
    if bounds.has_low and bounds.has_high:
        max_offset = _calculate_max_offset(bounds)
        strategies: list[Callable[[], int]] = [
            lambda: randint(bounds.low - max_offset, bounds.low - 1),
            lambda: randint(bounds.high + 1, bounds.high + max_offset),
        ]
        return choice(strategies)()

    if bounds.has_low and not bounds.has_high:
        max_offset = max(1, _calculate_max_offset(bounds))
        return randint(bounds.low - max_offset, bounds.low - 1)

    if bounds.has_high and not bounds.has_low:
        max_offset = max(1, _calculate_max_offset(bounds))
        return randint(bounds.high + 1, bounds.high + max_offset)

    raise ValueError("Cannot generate invalid integer: no bounds specified")


def _calculate_max_offset(bounds: Bounds) -> int:
    span = max(1, bounds.high - bounds.low)
    base = max(100, span * 2)
    return min(base, 10**6)


def _get_integer_valid_borders(constraints: Sequence[Constraint]) -> Bounds:
    low = -(2**63)
    high = 2**63 - 1
    has_low = False
    has_high = False

    for constraint in constraints:
        if not isinstance(
            constraint, (GreaterThan, GreaterOrEqual, LessThan, LessOrEqual)
        ):
            continue

        v = int(constraint.value)
        match constraint:
            case GreaterThan():
                low = max(low, v + 1)
                has_low = True
            case GreaterOrEqual():
                low = max(low, v)
                has_low = True
            case LessThan():
                high = min(high, v - 1)
                has_high = True
            case LessOrEqual():
                high = min(high, v)
                has_high = True
    if low > high:
        raise ValueError(
            f"Min value cannot be higher than max value: min: {low}, high {high}"
        )
    return Bounds(low, high, has_low, has_high)
