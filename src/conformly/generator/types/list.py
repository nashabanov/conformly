from typing import Any

from ...resolver.semantics import ListSemantic
from ...types import _UNSET, ViolationType
from ..context import GenerationContext


def generate_value(
    ctx: GenerationContext, semantic: ListSemantic, violation: ViolationType | None
) -> list[Any]:
    from ...resolver import ResolvedField
    from ...specs import FieldSpec
    from ..orchestration import generate_field

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
            default=_UNSET,
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
