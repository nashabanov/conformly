from .protocol import ParcingAdapterProtocol

from conformly.specs import ModelSpec

_adapters: list[ParcingAdapterProtocol] = []


def register(adapter: ParcingAdapterProtocol) -> None:
    _adapters.append(adapter)


def get_adapter(model: type) -> ParcingAdapterProtocol:
    for adapter in _adapters:
        if adapter.supports(model):
            return adapter
    raise TypeError(f"No adapters found for {model!r}")


def parse_model(model: type) -> ModelSpec:
    return get_adapter(model).parse(model)
