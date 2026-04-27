from collections.abc import Callable
from typing import Any

from ..extractors.constraints import split_collection_constraints
from ..extractors.types import DictNode, ListNode, ScalarNode, TypeNode, normalize_type
from ..models import ElementSpec, FieldSpec

from conformly._internal.constraints import Constraint


def build_field_spec(
    *,
    name: str,
    field_type: Any,
    default: Any,
    external_constraints: tuple[Constraint, ...],
    resolve_element: Callable[[TypeNode, str, tuple[Constraint, ...]], ElementSpec],
) -> FieldSpec:
    node = normalize_type(field_type, name)

    match node:
        case ScalarNode():
            return FieldSpec(
                name=name,
                element=resolve_element(node, name, external_constraints),
                default=default,
                nullable=node.nullable,
            )

        case ListNode():
            element_constraints, collection_constraints = split_collection_constraints(
                external_constraints
            )

            return FieldSpec(
                name=name,
                collection_type=node.origin,
                collection_constraints=(*node.constraints, *collection_constraints),
                item=resolve_element(node.item, name, element_constraints),
                default=default,
                nullable=node.nullable,
            )

        case DictNode():
            return FieldSpec(
                name=name,
                collection_type=dict,
                collection_constraints=node.constraints,
                key=resolve_element(node.key, name, external_constraints),
                value=resolve_element(node.value, name, external_constraints),
                default=default,
                nullable=node.nullable,
            )
