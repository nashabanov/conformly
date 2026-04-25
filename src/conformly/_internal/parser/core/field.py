from collections.abc import Callable
from typing import Any

from ..extractors.constraints import split_collection_constraints
from ..extractors.types import extract_container, is_nullable, unwrap_annotated
from ..models import ElementSpec, FieldSpec

from conformly._internal.constraints import Constraint
from conformly.exceptions import ResolutionError


def build_field_spec(
    *,
    name: str,
    field_type: Any,
    default: Any,
    external_constraints: tuple[Constraint, ...],
    resolve_element: Callable[[Any, str, tuple[Constraint, ...]], ElementSpec],
) -> FieldSpec:
    container = extract_container(field_type, name)
    nullable = is_nullable(field_type)

    element_constraints, collection_constraints = split_collection_constraints(
        external_constraints
    )

    if container["kind"] == "scalar":
        return FieldSpec(
            name=name,
            element=resolve_element(field_type, name, element_constraints),
            default=default,
            nullable=nullable,
        )

    elif container["kind"] == "list":
        item_type, item_constraints = unwrap_annotated(container["parts"]["item"])

        return FieldSpec(
            name=name,
            collection_type=container["origin"],
            collection_constraints=(
                *container["constraints"],
                *collection_constraints,
            ),
            item=resolve_element(
                item_type,
                name,
                (*element_constraints, *item_constraints),
            ),
            default=default,
            nullable=nullable,
        )

    elif container["kind"] == "dict":
        return FieldSpec(
            name=name,
            collection_type=container["origin"],
            collection_constraints=(
                *container["constraints"],
                *collection_constraints,
            ),
            key=resolve_element(container["parts"]["key"], name, element_constraints),
            value=resolve_element(
                container["parts"]["value"], name, element_constraints
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
