from ...resolver.semantics import NumericSemantic
from ...types import ViolationType
from ..context import GenerationContext


def generate_value(
    ctx: GenerationContext, semantic: NumericSemantic, violation: ViolationType | None
) -> int:
    if not violation:
        valid_range = semantic.valid_range
        return ctx.rng.randint(int(valid_range.min_value), int(valid_range.max_value))
    else:
        return _generate_invalid_integer(ctx, semantic, violation)


def _generate_invalid_integer(
    ctx: GenerationContext, semantic: NumericSemantic, violation: ViolationType
) -> int:
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
