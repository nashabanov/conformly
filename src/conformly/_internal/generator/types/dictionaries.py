from typing import Any, no_type_check

from ..context import GenerationContext

from conformly._internal.resolver.semantics import DictSemantic
from conformly._internal.types import ViolationType


@no_type_check
def generate_value(
    ctx: GenerationContext,
    semantic: DictSemantic,
    violation: ViolationType | None = None,
) -> dict[Any, Any]:
    return (
        _generate_valid_dict(ctx, semantic)
        if violation is None
        else _generate_invalid_dict(ctx, semantic, violation)
    )


def _generate_valid_dict(
    ctx: GenerationContext, semantic: DictSemantic
) -> dict[Any, Any]:
    return {"test": "valid"}


def _generate_invalid_dict(
    ctx: GenerationContext, semantic: DictSemantic, violation: ViolationType
) -> dict[Any, Any]:
    return {"test": "invalid"}
