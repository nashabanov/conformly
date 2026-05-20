from functools import lru_cache
from typing import (
    Any,
    NotRequired,
    Required,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

from ..core import build_element_spec, build_field_spec
from ..models import FieldSpec, ModelSpec

from conformly._internal.types.constants import UNSET
from conformly.exceptions import ResolutionError


def supports(model: type) -> bool:
    print(is_typeddict(model))
    return is_typeddict(model)


@lru_cache(maxsize=128)
def parse(model: type) -> ModelSpec:
    if not supports(model):
        raise ResolutionError(
            f"Unsupported model type: {model}",
            context={
                "code": "unsupported_model_type",
                "model": repr(model),
                "expected": "TypedDict",
            },
        )

    return ModelSpec(name=model.__name__, type="typeddict", fields=parse_fields(model))


def parse_fields(model: type) -> tuple[FieldSpec, ...]:
    type_hints = get_type_hints(model, include_extras=True)

    required = getattr(model, "__required_keys__", set(type_hints.keys()))

    return tuple(
        parse_field(
            name=name,
            field_type=resolve_type(type_hints, name),
            required=name in required,
        )
        for name in type_hints
    )


def resolve_type(type_hints: dict[str, Any], field_name: str) -> Any:
    t = type_hints[field_name]

    origin = get_origin(t)

    if origin is NotRequired or origin is Required:
        return get_args(t)[0]

    return t


def parse_field(name: str, field_type: Any, required: bool) -> FieldSpec:
    return build_field_spec(
        name=name,
        field_type=field_type,
        default=UNSET if required else None,
        external_constraints=(),
        resolve_element=lambda node, field_name, constraints: build_element_spec(
            node=node,
            field_name=field_name,
            extra_constraints=constraints,
            resolve_type=lambda x: x,
        ),
    )
