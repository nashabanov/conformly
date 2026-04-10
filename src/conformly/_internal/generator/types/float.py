import math

from ..context import GenerationContext

from conformly._internal.types import FLOAT_MAX, FLOAT_MIN, ViolationType
from conformly.resolver.semantics import NumericSemantic


def generate_value(
    ctx: GenerationContext, semantic: NumericSemantic, violation: ViolationType | None
) -> float:
    if violation is None:
        low, high = semantic.valid_range.min_value, semantic.valid_range.max_value

        if semantic.multiple_of is not None:
            multiple_of = float(semantic.multiple_of)
            first_multiple = math.ceil(low / multiple_of) * multiple_of
            last_multiple = math.floor(high / multiple_of) * multiple_of

            if first_multiple > last_multiple:
                raise ValueError(
                    f"Cannot generate valid float: no multiples of {multiple_of} "
                    f"in range [{low}, {high}]"
                )

            count = round((last_multiple - first_multiple) / multiple_of) + 1
            index = ctx.rng.randint(0, count - 1)
            return first_multiple + index * multiple_of

        else:
            if low == FLOAT_MIN or high == FLOAT_MAX:
                gen_low = max(low, -1e300)
                gen_high = min(high, 1e300)
                return ctx.rng.uniform(gen_low, gen_high)
            else:
                return ctx.rng.uniform(low, high)
    else:
        return _generate_invalid_float(ctx, semantic, violation)


def _generate_invalid_float(
    ctx: GenerationContext, semantic: NumericSemantic, violation: ViolationType
) -> float:
    if violation == ViolationType.NOT_MULTIPLE and semantic.multiple_of is not None:
        valid_range = semantic.valid_range
        min_val = float(valid_range.min_value)
        max_val = float(valid_range.max_value)
        multiple_of = float(semantic.multiple_of)

        base = ctx.rng.uniform(min_val, max_val)
        remainder = base % multiple_of
        epsilon = 1e-10

        if abs(remainder) < epsilon or abs(remainder - multiple_of) < epsilon:
            base += multiple_of / ctx.rng.randint(3, 10)
            if base > max_val:
                base = max_val - epsilon
            elif base < min_val:
                base = min_val + epsilon

        return base

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
