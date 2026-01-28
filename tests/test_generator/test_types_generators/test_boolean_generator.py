from conformly.generator.types.boolean import generate_value
from conformly.types import FieldKind


def test_generate():
    assert type(generate_value(semantic=FieldKind.BOOLEAN)) is bool
