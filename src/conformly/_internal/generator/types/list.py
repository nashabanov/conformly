from typing import Any

from .._errors import generation_error
from ..context import GenerationContext
from ._utils import (
    calculate_valid_collection_range,
    collection_retry_error,
    generate_collection_item,
    is_hashable,
    unique_collection_range,
)

from conformly._internal.planner.model import CollectionTarget
from conformly._internal.resolver.semantics import ListSemantic
from conformly._internal.types import FieldPath, ViolationType


def generate_value(
    ctx: GenerationContext,
    semantic: ListSemantic,
    violation: ViolationType | None,
    *,
    target: CollectionTarget | None = None,
    overrides: dict[FieldPath, Any] | None = None,
) -> list[Any]:
    return (
        _generate_valid_list(ctx, semantic, overrides=overrides)
        if not violation
        else _generate_invalid_list(
            ctx, semantic, violation, target, overrides=overrides
        )
    )


def _generate_valid_list(
    ctx: GenerationContext,
    semantic: ListSemantic,
    overrides: dict[FieldPath, Any] | None = None,
) -> list[Any]:
    min_len, max_len = calculate_valid_collection_range(semantic)

    if semantic.is_unique_items:
        min_len, max_len = unique_collection_range(
            min_len, max_len, semantic.element_semantic, collection="list"
        )
    length = ctx.rng.randint(min_len, max_len)
    return _generate_list_of_length(ctx, semantic, length, overrides=overrides)


def _generate_list_of_length(
    ctx: GenerationContext,
    semantic: ListSemantic,
    length: int,
    overrides: dict[FieldPath, Any] | None = None,
) -> list[Any]:
    if not semantic.is_unique_items:
        return [
            generate_collection_item(
                ctx,
                semantic.element_semantic,
                semantic.element_nested_model,
                None,
                overrides=overrides,
            )
            for _ in range(length)
        ]

    result: list[Any] = []
    seen: set[Any] = set()
    unhashable: list[Any] = []
    max_attempts = max(100, length * 20)
    for _ in range(max_attempts):
        if len(result) == length:
            return result
        item = generate_collection_item(
            ctx,
            semantic.element_semantic,
            semantic.element_nested_model,
            None,
            overrides=overrides,
        )
        if is_hashable(item):
            if item in seen or item in unhashable:
                continue
            seen.add(item)
        else:
            if item in result:
                continue
            unhashable.append(item)
        result.append(item)
    if len(result) == length:
        return result
    raise collection_retry_error(
        collection="list",
        requested_size=length,
        generated_size=len(result),
        attempts=max_attempts,
    )


def _generate_invalid_list(
    ctx: GenerationContext,
    semantic: ListSemantic,
    violation: ViolationType,
    target: CollectionTarget | None,
    overrides: dict[FieldPath, Any] | None = None,
) -> list[Any]:
    min_len, max_len = calculate_valid_collection_range(semantic)
    if violation == ViolationType.TOO_LESS_ITEMS:
        lower = semantic.length_range.min_length if semantic.length_range else min_len
        return _generate_list_of_length(
            ctx, semantic, max(0, lower - 1), overrides=overrides
        )
    if violation == ViolationType.TOO_MANY_ITEMS:
        return _generate_list_of_length(ctx, semantic, max_len + 1, overrides=overrides)
    if violation == ViolationType.DUPLICATE:
        if max_len < 2:
            raise generation_error(
                "No room for duplicate elements", code="invalid_collection_target"
            )
        length = ctx.rng.randint(max(2, min_len), max_len)
        # Each element remains valid; the selected container violates uniqueness.
        result = [
            generate_collection_item(
                ctx,
                semantic.element_semantic,
                semantic.element_nested_model,
                None,
                overrides=overrides,
            )
            for _ in range(length - 1)
        ]
        return [*result, result[0]]
    if target is None or target.side != "element":
        raise generation_error(
            "List element violation requires a planned target",
            code="missing_collection_target",
        )
    if semantic.is_unique_items:
        min_len, max_len = unique_collection_range(
            min_len,
            max_len,
            semantic.element_semantic,
            collection="list",
            extra_values=1,
        )
    length = ctx.rng.randint(min_len, max_len)
    if not 0 <= target.index < length:
        raise generation_error(
            "List target is outside collection",
            code="invalid_collection_target",
            index=target.index,
            size=length,
        )
    result = _generate_list_of_length(ctx, semantic, length - 1, overrides=overrides)
    item = generate_collection_item(
        ctx,
        semantic.element_semantic,
        semantic.element_nested_model,
        (violation,),
        overrides=overrides,
    )
    result.insert(target.index, item)
    return result
