import math
from random import uniform

from ...resolver.semantics import NumericSemantic
from ...types import FLOAT_MAX, FLOAT_MIN, ViolationType


def generate_value(semantic: NumericSemantic, violation: ViolationType | None) -> float:
    if violation is None:
        low, high = semantic.valid_range.min_value, semantic.valid_range.max_value

        if low == FLOAT_MIN or high == FLOAT_MAX:
            gen_low = max(low, -1e300)
            gen_high = min(high, 1e300)
            return uniform(gen_low, gen_high)
        else:
            return uniform(low, high)
    else:
        return _generate_invalid_float(semantic, violation)


def _generate_invalid_float(
    semantic: NumericSemantic, violation: ViolationType
) -> float:
    for r in semantic.invalid_ranges:
        if (
            violation == ViolationType.BELOW_MIN
            and r.max_value <= semantic.valid_range.min_value
        ):
            if math.isfinite(r.max_value):
                return math.nextafter(r.max_value, -math.inf)
            else:
                return -1e308
        if (
            violation == ViolationType.ABOVE_MAX
            and r.min_value >= semantic.valid_range.max_value
        ):
            if math.isfinite(r.min_value):
                return math.nextafter(r.min_value, math.inf)
            else:
                return 1e308

    raise ValueError(f"No invalid ranges available for violation: {violation}")
