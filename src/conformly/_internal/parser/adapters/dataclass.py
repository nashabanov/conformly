from dataclasses import MISSING, Field, fields, is_dataclass
from functools import lru_cache
from typing import (
    Any,
    get_type_hints,
)

from ...types import ENUMERATED_TYPE, UNSET
from ..extractors.constraints import (
    is_constraints_consistent,
    parse_annotated_constraints,
    parse_metadata_constraints,
    split_collection_constraints,
)
from ..extractors.types import (
    extract_container,
    extract_runtime_type_and_constraints,
    is_nullable,
    unwrap_annotated,
)
from ..models import ElementSpec, FieldSpec, ModelSpec

from conformly._internal.constraints import Constraint
from conformly.exceptions import ResolutionError, SchemaError


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
    container = extract_container(field_type, field.name)
    default = parse_defaults(field)
    nullable = is_nullable(field_type)

    external_constraints = (
        *parse_annotated_constraints(field_type),
        *parse_metadata_constraints(field.metadata),
    )

    element_constraints, collection_constraints = split_collection_constraints(
        external_constraints
    )

    if container["kind"] == "scalar":
        return FieldSpec(
            name=field.name,
            element=parse_element(field_type, field.name, element_constraints),
            default=default,
            nullable=nullable,
        )

    elif container["kind"] == "list":
        item_type, item_constraints = unwrap_annotated(container["parts"]["item"])
        all_collection_constraints = (
            *container["constraints"],
            *collection_constraints,
        )
        return FieldSpec(
            name=field.name,
            collection_type=container["origin"],
            collection_constraints=all_collection_constraints,
            item=parse_element(
                item_type, field.name, (*element_constraints, *item_constraints)
            ),
            default=default,
            nullable=nullable,
        )

    elif container["kind"] == "dict":
        all_collection_constraints = (
            *container["constraints"],
            *collection_constraints,
        )
        return FieldSpec(
            name=field.name,
            collection_type=container["origin"],
            collection_constraints=all_collection_constraints,
            key=parse_element(
                container["parts"]["key"], field.name, element_constraints
            ),
            value=parse_element(
                container["parts"]["value"], field.name, element_constraints
            ),
            default=default,
            nullable=nullable,
        )

    raise ResolutionError(
        f"Unsupported field type: {field_type}",
        context={
            "code": "unsupported_field_type",
            "field_type": repr(field_type),
        },
    )


def parse_element(
    field_type: Any, field_name: str, extra_constraints: tuple[Constraint, ...]
) -> ElementSpec:
    runtime_type, intrinsic_constraints = extract_runtime_type_and_constraints(
        field_type, field_name
    )

    all_constraints = (
        *intrinsic_constraints,
        *extra_constraints,
    )

    if not is_constraints_consistent(all_constraints):
        raise SchemaError(
            f"Field '{field_name}': incompatible constraints",
            context={
                "code": "inconsistent_constraints",
                "field_name": field_name,
                "constraints": [type(c).__name__ for c in all_constraints],
                "reason": "closed set cannot be combined with other constraints",
            },
        )

    nested_model = (
        parse(runtime_type)
        if runtime_type is not ENUMERATED_TYPE and supports(runtime_type)
        else None
    )

    return ElementSpec(
        field_type=runtime_type,
        constraints=all_constraints,
        nested_model=nested_model,
    )


def parse_defaults(field: Field[Any]) -> Any:
    if field.default is not MISSING:
        return field.default

    elif field.default_factory is not MISSING:
        return field.default_factory

    return UNSET
