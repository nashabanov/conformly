from typing import Any

from .._errors import generation_error
from ..context import GenerationContext

from conformly._internal.resolver import ResolvedModel
from conformly._internal.resolver.semantics import (
    BooleanSemantic,
    DictSemantic,
    EnumSemantic,
    FieldSemantics,
    ListSemantic,
    NumericSemantic,
    TupleSemantic,
)
from conformly._internal.types import UNSET, FieldKind, ViolationType
from conformly.exceptions import GenerationError


def calculate_valid_collection_range(
    semantic: ListSemantic | DictSemantic | TupleSemantic,
) -> tuple[int, int]:
    """Choose a small default range without overriding declared size limits."""
    if semantic.length_range is None:
        return 1, 3
    lower = semantic.length_range.min_length
    upper = semantic.length_range.max_length
    if upper == 0:
        return lower, 0
    lower = max(1, lower)
    return lower, upper if upper is not None else max(3, lower)


def finite_cardinality(semantic: FieldSemantics) -> int | None:
    if isinstance(semantic, BooleanSemantic):
        return 2
    if isinstance(semantic, EnumSemantic):
        # Equality, rather than type or identity, determines collection uniqueness.
        values: list[Any] = []
        for value in semantic.values:
            if value not in values:
                values.append(value)
        return len(values)
    if isinstance(semantic, NumericSemantic) and semantic.kind == FieldKind.INTEGER:
        lower = int(semantic.valid_range.min_value)
        upper = int(semantic.valid_range.max_value)
        step = int(semantic.multiple_of) if semantic.multiple_of is not None else 1
        if step > 0:
            return max(0, upper // step - (lower - 1) // step)
    return None


def unique_collection_range(
    lower: int, upper: int, semantic: FieldSemantics, *, collection: str
) -> tuple[int, int]:
    cardinality = finite_cardinality(semantic)
    if cardinality is not None:
        if lower > cardinality:
            raise generation_error(
                "Collection size exceeds the number of distinct valid values",
                code="impossible_collection_size",
                collection=collection,
                requested_size=lower,
                cardinality=cardinality,
            )
        upper = min(upper, cardinality)
    return lower, upper


def collection_retry_error(
    *, collection: str, requested_size: int, generated_size: int, attempts: int
) -> GenerationError:
    return generation_error(
        "Could not fill collection with distinct valid values",
        code="collection_retry_exhausted",
        collection=collection,
        requested_size=requested_size,
        generated_size=generated_size,
        attempts=attempts,
    )


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
