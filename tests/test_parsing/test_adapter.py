import pytest

from dataspec.parsing.registry import get_adapter, parse_model, register
from dataspec.specs.model import ModelSpec


class DummyAdapter:
    def supports(self, model):
        return model is str

    def parse(self, model):
        return ModelSpec(name=f"{model}", type="dataclass", fields=[])


def test_register_and_get_adapter():
    register(DummyAdapter())
    adapter = get_adapter(str)
    assert isinstance(adapter, DummyAdapter)


def test_register_adapter_and_parse_model():
    register(DummyAdapter())
    parsed_model = parse_model(str)
    assert isinstance(parsed_model, ModelSpec)


def test_adapter_not_found():
    with pytest.raises(TypeError):
        get_adapter(int)


def test_adapter_not_found_on_parse_model_call():
    with pytest.raises(TypeError):
        parse_model(int)
