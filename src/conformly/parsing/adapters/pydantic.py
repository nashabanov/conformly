from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...specs import FieldSpec, ModelSpec

if TYPE_CHECKING:
    from pydantic import BaseModel


def supports(model: type) -> bool:
    return hasattr(model, "__pydantic_validator__")


def parse(model: type) -> ModelSpec:
    try:
        from pydantic import BaseModel
        from pydantic_core import PydanticUndefined
    except ImportError:
        raise ImportError(
            "Pydantic adapter requires 'pydantic' package. "
            "Install with: pip install 'conformly[pydantic]'"
        ) from None

    if not issubclass(model, BaseModel):
        raise TypeError(
            f"Unsupported model type: {model}. Expected Pydantic BaseModel."
        )

    return ModelSpec(
        name=model.__name__,
        type="pydantic",
        fields=parse_fields(model, PydanticUndefined),
    )


def parse_fields(
    model: type[BaseModel], PydanticUndefined: Any
) -> tuple[FieldSpec, ...]:
    return ()
