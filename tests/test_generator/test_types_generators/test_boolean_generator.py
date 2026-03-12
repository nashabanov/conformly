from conformly.generator.context import GenerationContext
from conformly.generator.types.boolean import generate_value
from conformly.types import FieldKind


def test_generate(ctx: GenerationContext) -> None:
    assert type(generate_value(ctx=ctx, semantic=FieldKind.BOOLEAN)) is bool
