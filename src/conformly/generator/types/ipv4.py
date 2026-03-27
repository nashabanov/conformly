from ...resolver.semantics import StringSemantic
from ...types import ViolationType
from ..context import GenerationContext


def generate_value(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType | None = None,
) -> str:
    return (
        _generate_valid_ipv4(ctx, semantic)
        if violation is None
        else _generate_invalid_ipv4(ctx, semantic, violation)
    )


def _generate_valid_ipv4(ctx: GenerationContext, semantic: StringSemantic) -> str: ...


def _generate_invalid_ipv4(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType,
) -> str: ...
