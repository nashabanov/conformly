from typing import no_type_check

from ..context import GenerationContext

from conformly._internal.resolver.semantics import FieldSemantics
from conformly._internal.types import ViolationType


@no_type_check
def generate_value(
    ctx: GenerationContext,
    semantic: FieldSemantics,
    violation: ViolationType | None = None,
) -> bool:
    return ctx.rng.choice([True, False])
