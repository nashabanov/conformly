from .protocol import ParcingAdapterProtocol

from conformly.exceptions import ResolutionError

_adapters: list[ParcingAdapterProtocol] = []


def register(adapter: ParcingAdapterProtocol) -> None:
    _adapters.append(adapter)


def get_adapter(model: type) -> ParcingAdapterProtocol:
    for adapter in _adapters:
        if adapter.supports(model):
            return adapter
    raise ResolutionError(
        f"No adapters found for {model!r}",
        context={
            "code": "adapter_not_found",
            "model": repr(model),
            "registred_adapters": [type(a).__name__ for a in _adapters],
        },
    )


def get_adapter_or_none(model: type) -> ParcingAdapterProtocol | None:
    for adapter in _adapters:
        if adapter.supports(model):
            return adapter
    return None
