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
from conformly._internal.resolver.semantics import DictSemantic
from conformly._internal.types import UNSET, ViolationType


def generate_value(
    ctx: GenerationContext,
    semantic: DictSemantic,
    violation: ViolationType | None = None,
    *,
    target: CollectionTarget | None = None,
) -> dict[Any, Any]:
    return (
        _generate_valid_dict(ctx, semantic)
        if violation is None
        else _generate_invalid_dict(ctx, semantic, violation, target)
    )


def _generate_valid_dict(
    ctx: GenerationContext, semantic: DictSemantic
) -> dict[Any, Any]:
    min_len, max_len = calculate_valid_collection_range(semantic)

    min_len, max_len = unique_collection_range(
        min_len, max_len, semantic.key_semantic, collection="dict"
    )
    length = ctx.rng.randint(min_len, max_len)
    return _generate_dict_of_length(ctx, semantic, length)


def _generate_dict_of_length(
    ctx: GenerationContext,
    semantic: DictSemantic,
    length: int,
    violation: ViolationType | None = None,
    target: CollectionTarget | None = None,
    target_value: Any = UNSET,
) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    max_attempts = max(100, length * 20)
    for _ in range(max_attempts):
        if len(result) == length:
            return result
        is_target = target is not None and len(result) == target.index
        key_violation = (
            (violation,)
            if is_target
            and target is not None
            and target.side == "key"
            and violation is not None
            else None
        )
        value_violation = (
            (violation,)
            if is_target
            and target is not None
            and target.side == "value"
            and violation is not None
            else None
        )
        key = generate_collection_item(ctx, semantic.key_semantic, None, key_violation)
        if not is_hashable(key) or key in result:
            continue
        result[key] = (
            target_value
            if is_target and target_value is not UNSET
            else generate_collection_item(
                ctx,
                semantic.value_semantic,
                semantic.value_nested_model,
                value_violation,
            )
        )
    if len(result) == length:
        return result
    raise collection_retry_error(
        collection="dict",
        requested_size=length,
        generated_size=len(result),
        attempts=max_attempts,
    )


def _generate_invalid_dict(
    ctx: GenerationContext,
    semantic: DictSemantic,
    violation: ViolationType,
    target: CollectionTarget | None,
) -> dict[Any, Any]:
    min_len, max_len = calculate_valid_collection_range(semantic)
    if violation == ViolationType.TOO_LESS_ITEMS:
        lower = semantic.length_range.min_length if semantic.length_range else min_len
        length = max(0, lower - 1)
        unique_collection_range(
            length, length, semantic.key_semantic, collection="dict"
        )
        return _generate_dict_of_length(ctx, semantic, length)
    if violation == ViolationType.TOO_MANY_ITEMS:
        length = max_len + 1
        unique_collection_range(
            length, length, semantic.key_semantic, collection="dict"
        )
        return _generate_dict_of_length(ctx, semantic, length)
    if target is None or target.side not in ("key", "value"):
        raise generation_error(
            "Dictionary violation requires a planned key or value target",
            code="missing_collection_target",
        )
    min_len, max_len = unique_collection_range(
        min_len,
        max_len,
        semantic.key_semantic,
        collection="dict",
        extra_values=1 if target.side == "key" else 0,
    )
    length = ctx.rng.randint(min_len, max_len)
    if not 0 <= target.index < length:
        raise generation_error(
            "Dictionary target is outside collection",
            code="invalid_collection_target",
            index=target.index,
            size=length,
        )
    return _generate_dict_of_length(ctx, semantic, length, violation, target)
