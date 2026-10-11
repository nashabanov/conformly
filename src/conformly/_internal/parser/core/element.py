from collections.abc import Callable
from typing import Any

from ..adapters.registry import get_adapter_or_none
from ..extractors.constraints import is_constraints_consistent
from ..extractors.types import TypeNode
from ..models import ElementSpec

from conformly._internal.constraints import Constraint
from conformly._internal.types.constants import ENUMERATED_TYPE
from conformly.exceptions import SchemaError


def build_element_spec(
    *,
    node: TypeNode,
    field_name: str,
    extra_constraints: tuple[Constraint, ...],
    resolve_type: Callable[[Any], Any],
) -> ElementSpec:
    runtime_type = resolve_type(node.runtime_type)

    all_constraints = (*node.constraints, *extra_constraints)

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

    adapter = get_adapter_or_none(runtime_type)

    nested_model = (
        None
        if runtime_type is ENUMERATED_TYPE or adapter is None
        else adapter.parse(runtime_type)
    )

    return ElementSpec(
        field_type=runtime_type,
        constraints=all_constraints,
        nested_model=nested_model,
    )
