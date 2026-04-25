from collections.abc import Callable
from typing import Any

from ..extractors.constraints import is_constraints_consistent
from ..extractors.types import extract_runtime_type_and_constraints
from ..models import ElementSpec, ModelSpec

from conformly._internal.constraints import Constraint
from conformly._internal.types.constants import ENUMERATED_TYPE
from conformly.exceptions import SchemaError


def build_element_spec(
    *,
    field_type: Any,
    field_name: str,
    extra_constraints: tuple[Constraint, ...],
    resolve_type: Callable[[Any], Any],
    parse_model: Callable[[type], ModelSpec],
    supports_model: Callable[[type], bool],
) -> ElementSpec:
    runtime_type, instrinsic_constraints = extract_runtime_type_and_constraints(
        field_type, field_name
    )

    runtime_type = resolve_type(runtime_type)

    all_constraints = (*instrinsic_constraints, *extra_constraints)

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
        parse_model(runtime_type)
        if runtime_type is not ENUMERATED_TYPE and supports_model(runtime_type)
        else None
    )

    return ElementSpec(
        field_type=runtime_type,
        constraints=all_constraints,
        nested_model=nested_model,
    )
