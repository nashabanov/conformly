from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any, get_type_hints

from ..core import build_element_spec, build_field_spec
from ..models import FieldSpec, ModelSpec

from conformly._internal.types.constants import UNSET
from conformly.exceptions import ResolutionError

if TYPE_CHECKING:
    from attrs import Attribute


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

    return ModelSpec(
        name=model.__name__,
        type="attrs",
        fields=parse_fields(model),
    )


def parse_fields(model: type) -> tuple[FieldSpec, ...]:
    import attrs

    type_hints = get_type_hints(model, include_extras=True)

    attrs_fields = attrs.fields(model)

    return tuple(
        parse_field(attr, resolve_type(type_hints, attr.name)) for attr in attrs_fields
    )


def resolve_type(type_hints: dict[str, Any], field_name: str) -> Any:
    return type_hints[field_name]


def parse_field(attr: Attribute[Any], field_type: Any) -> FieldSpec:
    return build_field_spec(
        name=attr.name,
        field_type=field_type,
        default=parse_defaults(attr),
        external_constraints=(),
        resolve_element=lambda node, field_name, constraints: build_element_spec(
            node=node,
            field_name=field_name,
            extra_constraints=constraints,
            resolve_type=lambda x: x,
        ),
    )


def parse_defaults(attr: Any) -> Any:
    import attrs

    if attr.default is attrs.NOTHING:
        return UNSET

    if type(attr.default).__name__ == "Factory":
        return attr.default

    return attr.default
