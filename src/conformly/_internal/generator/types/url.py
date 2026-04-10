from ..context import GenerationContext

from conformly._internal.resolver.semantics import StringSemantic
from conformly._internal.types import FieldKind, ViolationType


def generate_value(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType | None = None,
) -> str:
    return (
        _generate_valid_url(ctx, semantic.kind)
        if violation is None
        else _generate_invalid_url(ctx, semantic.kind, violation)
    )


def _generate_valid_url(ctx: GenerationContext, kind: FieldKind) -> str:
    return "valid"


def _generate_invalid_url(
    ctx: GenerationContext, kind: FieldKind, violation: ViolationType
) -> str:
    return "invalid"
