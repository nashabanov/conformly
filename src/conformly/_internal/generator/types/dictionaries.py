from typing import Any

from ..context import GenerationContext
from ._utils import (
    calculate_valid_collection_range,
    generate_collection_item,
    is_hashable,
)

from conformly._internal.resolver.semantics import DictSemantic
from conformly._internal.types import ViolationType


def generate_value(
    ctx: GenerationContext,
    semantic: DictSemantic,
    violation: ViolationType | None = None,
) -> dict[Any, Any]:
    return (
        _generate_valid_dict(ctx, semantic)
        if violation is None
        else _generate_invalid_dict(ctx, semantic, violation)
    )


def _generate_valid_dict(
    ctx: GenerationContext, semantic: DictSemantic
) -> dict[Any, Any]:
    min_len, max_len = calculate_valid_collection_range(semantic)

    length = ctx.rng.randint(min_len, max_len)

    result: dict[Any, Any] = {}
    seen_keys = set()

    max_attempts = 20

    while len(result) < length and max_attempts > 0:
        key = generate_collection_item(ctx, semantic.key_semantic, None, None)

        if not is_hashable(key):
            max_attempts -= 1
            continue

        if key in seen_keys:
            max_attempts -= 1
            continue

        value = generate_collection_item(
            ctx, semantic.value_semantic, semantic.value_nested_model, None
        )

        seen_keys.add(key)
        result[key] = value

        max_attempts -= 1

    return result


def _generate_invalid_dict(
    ctx: GenerationContext, semantic: DictSemantic, violation: ViolationType
) -> dict[Any, Any]:
    min_len, max_len = calculate_valid_collection_range(semantic)

    match violation:
        case ViolationType.TOO_LESS_ITEMS:
            length = max(0, min_len - 1)
            return {
                generate_collection_item(
                    ctx, semantic.key_semantic, None, None
                ): generate_collection_item(
                    ctx, semantic.value_semantic, semantic.value_nested_model, None
                )
                for _ in range(length)
            }

        case ViolationType.TOO_MANY_ITEMS:
            length = max_len + 1
            return {
                generate_collection_item(
                    ctx, semantic.key_semantic, None, None
                ): generate_collection_item(
                    ctx, semantic.value_semantic, semantic.value_nested_model, None
                )
                for _ in range(length)
            }

        case _:
            length = ctx.rng.randint(min_len, max_len)
            result: dict[Any, Any] = {}

            for i in range(length):
                key_violation = None
                value_violation = None

                if i == 0:
                    if ctx.rng.choice([True, False]):
                        key_violation = (violation,)
                    else:
                        value_violation = (violation,)

                key = generate_collection_item(
                    ctx,
                    semantic.key_semantic,
                    None,
                    key_violation,
                )

                if not is_hashable(key) or key in result:
                    continue

                value = generate_collection_item(
                    ctx,
                    semantic.value_semantic,
                    semantic.value_nested_model,
                    value_violation,
                )

                result[key] = value

            return result
