from typing import Any

from ..context import GenerationContext

from conformly._internal.resolver import ResolvedModel
from conformly._internal.resolver.semantics import (
    DictSemantic,
    FieldSemantics,
    ListSemantic,
)
from conformly._internal.types import UNSET, ViolationType


def calculate_valid_collection_range(
    semantic: ListSemantic | DictSemantic,
) -> tuple[int, int]:
    if semantic.length_range is None:
        min_len = 1
        max_len = 3
    else:
        min_len = semantic.length_range.min_length or 1
        max_len = semantic.length_range.max_length or 3

    if min_len == 0:
        min_len = 1

    return min_len, max_len


def is_hashable(value: Any) -> bool:
    try:
        hash(value)
        return True
    except TypeError:
        return False


def generate_collection_item(
    ctx: GenerationContext,
    item_semantic: FieldSemantics,
    item_nested_model: ResolvedModel | None,
    violations: tuple[ViolationType, ...] | None,
) -> Any:
    from ..orchestration import generate_field

    from conformly._internal.parser import ElementSpec, FieldSpec
    from conformly._internal.resolver import ResolvedField

    mock_spec = FieldSpec(
        name="__list_item",
        element=ElementSpec(object, ()),
        default=UNSET,
        nullable=False,
    )

    elem_field = ResolvedField(
        field_spec=mock_spec,
        path=(),
        semantic=item_semantic,
        nested_model=item_nested_model,
    )

    return generate_field(ctx, elem_field, violations)
