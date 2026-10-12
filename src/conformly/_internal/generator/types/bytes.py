from .._errors import generation_error
from ..context import GenerationContext

from conformly._internal.resolver.semantics import BytesSemantic
from conformly._internal.types import ViolationType


def generate_value(
    ctx: GenerationContext, semantic: BytesSemantic, violation: ViolationType | None
) -> bytes:
    lower = semantic.length_range.min_length
    upper = semantic.length_range.max_length
    if violation is None:
        length = ctx.rng.randint(lower, upper if upper is not None else lower + 50)
    elif violation == ViolationType.TOO_SHORT and lower > 0:
        length = lower - 1
    elif violation == ViolationType.TOO_LONG and upper is not None:
        length = upper + 1
    else:
        raise generation_error(
            "Unsupported bytes violation",
            code="unsupported_violation",
            violation=violation.value,
        )
    return ctx.rng.randbytes(length)
