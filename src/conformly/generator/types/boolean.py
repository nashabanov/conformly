from typing import no_type_check

from ..._internal.types import ViolationType
from ...resolver.semantics import FieldSemantics
from ..context import GenerationContext


@no_type_check
def generate_value(
    ctx: GenerationContext,
    semantic: FieldSemantics,
    violation: ViolationType | None = None,
) -> bool:
    return ctx.rng.choice([True, False])
