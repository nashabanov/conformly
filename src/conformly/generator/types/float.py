from __future__ import annotations

from dataclasses import dataclass
import math
from random import choice, uniform
import sys
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


# INFO: Текущее ограничение нет поддержки nan/inf в явном виде
def supports(field: FieldSpec) -> bool:
    return field.type is float


def generate_value(constraints: Sequence[Constraint], valid: bool) -> float:
    bounds = _get_float_valid_borders(constraints)
    if valid:
        low, high = bounds.low, bounds.high

        if low == -sys.float_info.max or high == sys.float_info.max:
            gen_low = max(low, -1e300)
            gen_high = min(high, 1e300)
            return uniform(gen_low, gen_high)
        else:
            return uniform(low, high)
    else:
        return _generate_invalid_float(bounds)


@dataclass(frozen=True)
class FBounds:
    low: float
    high: float


def _generate_invalid_float(bounds: FBounds) -> float:
    strategies: list[Callable[[], float]] = [
        lambda: math.nextafter(bounds.low, -math.inf),
        lambda: math.nextafter(bounds.high, math.inf),
    ]
    return choice(strategies)()


def _get_float_valid_borders(constraints: Sequence[Constraint]) -> FBounds:
    low = -sys.float_info.max
    high = sys.float_info.max

    for constraint in constraints:
        if not isinstance(
            constraint, (GreaterThan, GreaterOrEqual, LessThan, LessOrEqual)
        ):
            continue

        v = float(constraint.value)
        match constraint:
            case GreaterThan():
                low = max(low, math.nextafter(v, math.inf))
            case GreaterOrEqual():
                low = max(low, v)
            case LessThan():
                high = min(high, math.nextafter(v, -math.inf))
            case LessOrEqual():
                high = min(high, v)

    if low > high:
        raise ValueError(
            f"Min value cannot be higher than max value: min: {low}, high {high}"
        )
    return FBounds(low, high)
