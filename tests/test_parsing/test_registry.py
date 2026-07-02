import pytest

from conformly._internal.parser import ModelSpec, parse_model
from conformly._internal.parser.adapters.registry import get_adapter, register
from conformly.exceptions import ResolutionError


class DummyAdapter:
    def supports(self, model):
        return model is str

    def parse(self, model):
        return ModelSpec(name=f"{model}", type="dataclass", fields=())


@pytest.fixture(autouse=True)
def clean_registry():
    from conformly._internal.parser.adapters.registry import _adapters

    original = list(_adapters)

    _adapters.clear()
    yield

    _adapters[:] = original


def test_register_and_get_adapter():
    register(DummyAdapter())
    adapter = get_adapter(str)
    assert isinstance(adapter, DummyAdapter)


def test_register_adapter_and_parse_model():
    register(DummyAdapter())
    parsed_model = parse_model(str)
    assert isinstance(parsed_model, ModelSpec)


def test_adapter_not_found():
    with pytest.raises(ResolutionError):
        get_adapter(int)


def test_adapter_not_found_on_parse_model_call():
    with pytest.raises(ResolutionError):
        parse_model(int)
