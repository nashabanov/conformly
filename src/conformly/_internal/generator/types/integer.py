from ..context import GenerationContext

from conformly._internal.types import ViolationType
from conformly.resolver.semantics import NumericSemantic


def generate_value(
    ctx: GenerationContext, semantic: NumericSemantic, violation: ViolationType | None
) -> int:
    if not violation:
        valid_range = semantic.valid_range
        min_val = int(valid_range.min_value)
        max_val = int(valid_range.max_value)

        if semantic.multiple_of is not None:
            multiple_of = int(semantic.multiple_of)

            first_multiple = ((min_val + multiple_of - 1) // multiple_of) * multiple_of

            if first_multiple > max_val:
                raise ValueError(
                    f"Cannot generate valid integer: no multiples of {multiple_of} "
                    f"in range [{min_val}, {max_val}]"
                )

            count = (max_val - first_multiple) // multiple_of + 1

            index = ctx.rng.randint(0, count - 1)
            return first_multiple + index * multiple_of

        return ctx.rng.randint(min_val, max_val)

    else:
        return _generate_invalid_integer(ctx, semantic, violation)


def _generate_invalid_integer(
    ctx: GenerationContext, semantic: NumericSemantic, violation: ViolationType
) -> int:
    if violation == ViolationType.NOT_MULTIPLE and semantic.multiple_of is not None:
        valid_range = semantic.valid_range
        return (
            ctx.rng.randint(int(valid_range.min_value), int(valid_range.max_value))
            * int(semantic.multiple_of)
            + 1
        )

    for r in semantic.invalid_ranges:
        if (
            violation == ViolationType.BELOW_MIN
            and r.max_value <= semantic.valid_range.min_value
        ):
            return ctx.rng.randint(int(r.min_value), int(r.max_value))

        if (
            violation == ViolationType.ABOVE_MAX
            and r.min_value >= semantic.valid_range.max_value
        ):
            return ctx.rng.randint(int(r.min_value), int(r.max_value))

    raise ValueError("Cannot generate invalid integer: no bounds specified")
