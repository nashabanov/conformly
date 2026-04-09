from .adapters.registry import get_adapter
from .models import ModelSpec


def parse_model(model: type) -> ModelSpec:
    return get_adapter(model).parse(model)
