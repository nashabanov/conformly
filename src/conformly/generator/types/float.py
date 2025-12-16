from __future__ import annotations

from dataclasses import dataclass
import math
from random import choice, uniform
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from conformly.specs import ConstraintSpec, FieldSpec


# INFO: Текущее ограничение нет поддержки nan/inf в явном виде
def supports(field: FieldSpec) -> bool:
    return field.type is float


def generate_value(constraints: list[ConstraintSpec], valid: bool) -> float:
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


def _get_float_valid_borders(constraints: list[ConstraintSpec]) -> FBounds:
    low = -sys.float_info.max
    high = sys.float_info.max

    for c in constraints:
        v = float(c.value)
        match c.constraint_type:
            case "gt":
                low = max(low, math.nextafter(v, math.inf))
            case "ge":
                low = max(low, v)
            case "lt":
                high = min(high, math.nextafter(v, -math.inf))
            case "le":
                high = min(high, v)

    if low > high:
        raise ValueError(
            f"Min value cannot be higher than max value: min: {low}, high {high}"
        )
    return FBounds(low, high)
