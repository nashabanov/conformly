from dataspec.parsing.adapter import Adapter
from dataspec.specs import ModelSpec

_adapters: list[Adapter] = []


def register(adapter: Adapter) -> None:
    _adapters.append(adapter)


def get_adapter(model: type) -> Adapter:
    for adapter in _adapters:
        if adapter.supports(model):
            return adapter
    raise TypeError(f"No adapters found for {model!r}")


def parse_model(model: type) -> ModelSpec:
    return get_adapter(model).parse(model)
