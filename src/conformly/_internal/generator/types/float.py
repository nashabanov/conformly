from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, localcontext
import math

from .._errors import generation_error
from ..context import GenerationContext

from conformly._internal.resolver.semantics import NumericSemantic
from conformly._internal.resolver.semantics._numeric import is_float_multiple
from conformly._internal.types import MAX_GENERATION_ATTEMPTS, ViolationType


def generate_value(
    ctx: GenerationContext, semantic: NumericSemantic, violation: ViolationType | None
) -> float:
    if violation is not None:
        return _generate_invalid_float(ctx, semantic, violation)

    low = float(semantic.valid_range.min_value)
    high = float(semantic.valid_range.max_value)
    if semantic.multiple_of is not None:
        divisor = float(semantic.multiple_of)
        # Decimal index arithmetic avoids dropping endpoints such as 0.3 / 0.1.
        with localcontext() as decimal_ctx:
            decimal_ctx.prec = 700
            step = Decimal(str(divisor))
            first = (
                int((Decimal(str(low)) / step).to_integral_value(ROUND_CEILING))
                if math.isfinite(low)
                else None
            )
            last = (
                int((Decimal(str(high)) / step).to_integral_value(ROUND_FLOOR))
                if math.isfinite(high)
                else None
            )
            if first is None:
                first = min(0, last or 0) - 1_000_000
            if last is None:
                last = max(0, first) + 1_000_000
            # Float rounding may move the boundary multiple outside the range.
            while first <= last and float(first * step) < low:
                first += 1
            while first <= last and float(last * step) > high:
                last -= 1
            if first <= last:
                for _ in range(MAX_GENERATION_ATTEMPTS):
                    value = float(ctx.rng.randint(first, last) * step)
                    if low <= value <= high and is_float_multiple(value, divisor):
                        return value
                raise generation_error(
                    "Could not generate a verified float multiple",
                    code="numeric_generation_exhausted",
                    attempts=MAX_GENERATION_ATTEMPTS,
                    multiple_of=divisor,
                    valid_range=[low, high],
                )
        raise generation_error(
            "Cannot generate valid float: no multiples of in valid range",
            code="no_multiples_of",
            multiple_of=divisor,
            valid_range=[low, high],
        )

    gen_low = low if math.isfinite(low) else min(-1e300, high)
    gen_high = high if math.isfinite(high) else max(1e300, low)
    # Weighted interpolation avoids overflow in high - low.
    weight = ctx.rng.random()
    value = (1 - weight) * gen_low + weight * gen_high
    if math.isfinite(value):
        value = max(gen_low, min(gen_high, value))
        if low <= value <= high:
            return value
    raise generation_error(
        "Could not generate a finite float within bounds",
        code="numeric_generation_exhausted",
        valid_range=[low, high],
    )


def _generate_invalid_float(
    ctx: GenerationContext, semantic: NumericSemantic, violation: ViolationType
) -> float:
    if violation == ViolationType.NOT_MULTIPLE and semantic.multiple_of is not None:
        divisor = float(semantic.multiple_of)
        # Other constraints on the selected target need not remain satisfied.
        for _ in range(MAX_GENERATION_ATTEMPTS):
            value = divisor * ctx.rng.uniform(0.1, 0.9)
            if math.isfinite(value) and not is_float_multiple(value, divisor):
                return value
        raise generation_error(
            "Could not generate a verified non-multiple",
            code="numeric_violation_exhausted",
            violation=violation.value,
            multiple_of=divisor,
            attempts=MAX_GENERATION_ATTEMPTS,
        )

    for r in semantic.invalid_ranges:
        if (
            violation == ViolationType.BELOW_MIN
            and r.max_value <= semantic.valid_range.min_value
        ):
            value = math.nextafter(float(r.max_value), -math.inf)
            if math.isfinite(value) and value < semantic.valid_range.min_value:
                return value
        if (
            violation == ViolationType.ABOVE_MAX
            and r.min_value >= semantic.valid_range.max_value
        ):
            value = math.nextafter(float(r.min_value), math.inf)
            if math.isfinite(value) and value > semantic.valid_range.max_value:
                return value

    raise generation_error(
        "Cannot generate invalid value: no finite invalid value available",
        code="no_invalid_ranges",
        violation=violation.value,
        valid_range=[semantic.valid_range.min_value, semantic.valid_range.max_value],
    )
