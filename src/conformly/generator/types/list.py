from typing import Any

from ...resolver.semantics import ListSemantic
from ...types import ViolationType
from ..context import GenerationContext


def generate_value(
    ctx: GenerationContext, semantic: ListSemantic, violation: ViolationType | None
) -> list[Any]:
    return []
