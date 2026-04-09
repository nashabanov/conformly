from .protocol import ParcingAdapterProtocol

_adapters: list[ParcingAdapterProtocol] = []


def register(adapter: ParcingAdapterProtocol) -> None:
    _adapters.append(adapter)


def get_adapter(model: type) -> ParcingAdapterProtocol:
    for adapter in _adapters:
        if adapter.supports(model):
            return adapter
    raise TypeError(f"No adapters found for {model!r}")
