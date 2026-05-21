from __future__ import annotations

from functools import lru_cache

from ..models import ModelSpec

from conformly.exceptions import ResolutionError


def supports(model: type) -> bool:
    return hasattr(model, "__attrs_attrs__")


@lru_cache(maxsize=128)
def parse(model: type) -> ModelSpec:
    try:
        import attrs
    except ImportError:
        raise ImportError(
            "Attrs adapter requires 'attrs' package. "
            "Install with: pip install 'conformly[attrs]'"
        ) from None

    if not attrs.has(model):
        raise ResolutionError(
            f"Unsupported model type: {model}",
            context={
                "code": "unsupported_model_type",
                "model": repr(model),
                "expected": "attrs class",
            },
        )

    return ModelSpec(name=model.__name__, type="attrs", fields=())
