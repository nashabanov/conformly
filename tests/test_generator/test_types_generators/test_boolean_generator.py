from conformly._internal.generator import GenerationContext
from conformly._internal.generator.types.boolean import generate_value
from conformly._internal.types import FieldKind


def test_generate(ctx: GenerationContext) -> None:
    assert type(generate_value(ctx=ctx, semantic=FieldKind.BOOLEAN)) is bool
