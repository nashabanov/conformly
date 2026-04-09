from conformly._internal.types import FieldKind
from conformly.generator.context import GenerationContext
from conformly.generator.types.boolean import generate_value


def test_generate(ctx: GenerationContext) -> None:
    assert type(generate_value(ctx=ctx, semantic=FieldKind.BOOLEAN)) is bool
