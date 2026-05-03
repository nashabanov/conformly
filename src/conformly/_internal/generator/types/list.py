from typing import Any

from ..context import GenerationContext
from ._utils import (
    calculate_valid_collection_range,
    generate_collection_item,
    is_hashable,
)

from conformly._internal.resolver.semantics import ListSemantic
from conformly._internal.types import ViolationType


def generate_value(
    ctx: GenerationContext, semantic: ListSemantic, violation: ViolationType | None
) -> list[Any]:
    return (
        _generate_valid_list(ctx, semantic)
        if not violation
        else _generate_invalid_list(ctx, semantic, violation)
    )


def _generate_valid_list(ctx: GenerationContext, semantic: ListSemantic) -> list[Any]:
    min_len, max_len = calculate_valid_collection_range(semantic)

    length = ctx.rng.randint(min_len, max_len)

    result: list[Any] = []

    if not semantic.is_unique_items:
        for _ in range(length):
            item = generate_collection_item(
                ctx, semantic.element_semantic, semantic.element_nested_model, None
            )
            result.append(item)

    seen = set()
    max_attempts = 20

    while len(result) < length and max_attempts > 0:
        item = generate_collection_item(
            ctx, semantic.element_semantic, semantic.element_nested_model, None
        )

        if not is_hashable(item):
            result.append(item)
            continue

        if item not in seen:
            seen.add(item)
            result.append(item)

        max_attempts -= 1

    return result


def _generate_invalid_list(
    ctx: GenerationContext, semantic: ListSemantic, violation: ViolationType
) -> list[Any]:
    min_len, max_len = calculate_valid_collection_range(semantic)

    result: list[Any] = []

    match violation:
        case ViolationType.TOO_LESS_ITEMS:
            length = max(0, min_len - 1)
            return [
                generate_collection_item(
                    ctx, semantic.element_semantic, semantic.element_nested_model, None
                )
                for _ in range(length)
            ]

        case ViolationType.TOO_MANY_ITEMS:
            length = max_len + 1
            return [
                generate_collection_item(
                    ctx, semantic.element_semantic, semantic.element_nested_model, None
                )
                for _ in range(length)
            ]

        case ViolationType.DUPLICATE:
            base = _generate_valid_list(ctx, semantic)

            if not base:
                item = generate_collection_item(
                    ctx, semantic.element_semantic, semantic.element_nested_model, None
                )
                return [item, item]

            duplicate_idx = ctx.rng.randint(0, len(base) - 1)
            base.append(base[duplicate_idx])

            return base

        case _:
            length = ctx.rng.randint(min_len, max_len)
            violate_idx = ctx.rng.randint(0, length - 1)
            for i in range(length):
                item_violation = (violation,) if i == violate_idx else None
                item = generate_collection_item(
                    ctx,
                    semantic.element_semantic,
                    semantic.element_nested_model,
                    item_violation,
                )
                result.append(item)

    return result
