from typing import Any

from .._errors import generation_error
from ..context import GenerationContext

from conformly._internal.resolver import ResolvedModel
from conformly._internal.resolver.semantics import (
    DictSemantic,
    FieldSemantics,
    ListSemantic,
    TupleSemantic,
)
from conformly._internal.resolver.semantics._domains import finite_cardinality
from conformly._internal.types import ViolationType
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


def unique_collection_range(
    lower: int,
    upper: int,
    semantic: FieldSemantics,
    *,
    collection: str,
    extra_values: int = 0,
) -> tuple[int, int]:
    cardinality = finite_cardinality(semantic)
    if cardinality is not None:
        cardinality += extra_values
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
    from ..orchestration import generate_semantic_value

    return generate_semantic_value(ctx, item_semantic, item_nested_model, violations)
