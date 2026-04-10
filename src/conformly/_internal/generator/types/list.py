from typing import Any

from ..context import GenerationContext

from conformly._internal.types import UNSET, ViolationType
from conformly.resolver.semantics import ListSemantic


def generate_value(
    ctx: GenerationContext, semantic: ListSemantic, violation: ViolationType | None
) -> list[Any]:
    from ..orchestration import generate_field

    from conformly._internal.parser import FieldSpec
    from conformly.resolver import ResolvedField

    length = ctx.rng.randint(1, 3)
    violate_idx = ctx.rng.randint(0, length - 1) if violation else None

    result: list[Any] = []

    for i in range(length):
        elem_violation = violation if i == violate_idx else None
        violations = (elem_violation,) if elem_violation else None

        mock_spec = FieldSpec(
            name="__list_item",
            field_type=object,
            constraints=(),
            default=UNSET,
            nullable=False,
        )

        elem_field = ResolvedField(
            field_spec=mock_spec,
            path=(),
            semantic=semantic.element_semantic,
            nested_model=semantic.element_nested_model,
        )

        value = generate_field(ctx, elem_field, violations)

        result.append(value)

    return result
