import pytest

from conformly.generator.types.boolean import generate_value, supports
from conformly.specs import FieldSpec


def test_supports_valid():
    assert supports(FieldSpec(name="is", type=bool))


@pytest.mark.parametrize("_type", [int, list, float, dict, str, set])
def test_supports_invalid(_type):
    assert not supports(FieldSpec(name="is", type=_type))


def test_generate():
    assert type(generate_value()) is bool
