from dataclasses import MISSING, Field, fields, is_dataclass
from functools import lru_cache
from typing import (
    Any,
    get_type_hints,
)

from ..core import build_element_spec, build_field_spec
from ..extractors.constraints import parse_metadata_constraints
from ..models import FieldSpec, ModelSpec

from conformly._internal.types import UNSET
from conformly.exceptions import ResolutionError


def supports(model: type) -> bool:
    return is_dataclass(model)


@lru_cache(maxsize=128)
def parse(model: type) -> ModelSpec:
    if not supports(model):
        raise ResolutionError(
            f"Unsupported model type: {model}",
            context={
                "code": "unsupported_model_type",
                "model": repr(model),
                "expected": "dataclass",
            },
        )

    return ModelSpec(name=model.__name__, type="dataclass", fields=parse_fields(model))


def parse_fields(model: type) -> tuple[FieldSpec, ...]:
    type_hints = get_type_hints(model, include_extras=True)
    return tuple(
        parse_field(field, resolve_type(type_hints, field.name))
        for field in fields(model)
    )


def resolve_type(type_hints: dict[str, Any], field_name: str) -> Any:
    return type_hints[field_name]


def parse_field(field: Field[Any], field_type: Any) -> FieldSpec:
    external_constraints = parse_metadata_constraints(field.metadata)

    return build_field_spec(
        name=field.name,
        field_type=field_type,
        default=parse_defaults(field),
        external_constraints=external_constraints,
        resolve_element=lambda node, field_name, constraints: build_element_spec(
            node=node,
            field_name=field_name,
            extra_constraints=constraints,
            resolve_type=lambda x: x,
            parse_model=parse,
            supports_model=supports,
        ),
    )


def parse_defaults(field: Field[Any]) -> Any:
    if field.default is not MISSING:
        return field.default

    elif field.default_factory is not MISSING:
        return field.default_factory

    return UNSET
