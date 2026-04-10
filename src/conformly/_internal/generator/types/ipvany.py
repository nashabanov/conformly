from ..context import GenerationContext
from . import ipv4, ipv6

from conformly._internal.types import ViolationType
from conformly.resolver.semantics import StringSemantic


def generate_value(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType | None = None,
) -> str:
    if ctx.rng.random() < 0.5:
        return ipv4.generate_value(ctx, semantic, violation)
    else:
        return ipv6.generate_value(ctx, semantic, violation)
