from typing import Any

from .._errors import generation_error
from ..context import GenerationContext
from ._utils import calculate_valid_collection_range, generate_collection_item

from conformly._internal.planner.model import CollectionTarget
from conformly._internal.resolver.semantics import TupleSemantic
from conformly._internal.types import ViolationType


def generate_value(
    ctx: GenerationContext,
    semantic: TupleSemantic,
    violation: ViolationType | None = None,
    *,
    target: CollectionTarget | None = None,
) -> tuple[Any, ...]:
    if violation is None:
        return _generate_valid_tuple(ctx, semantic)

    return _generate_invalid_tuple(ctx, semantic, violation, target)


def _generate_valid_tuple(
    ctx: GenerationContext, semantic: TupleSemantic
) -> tuple[Any, ...]:
    if not semantic.is_variadic:
        elements = semantic.elements_semantics
    else:
        min_len, max_len = calculate_valid_collection_range(semantic)
        length = ctx.rng.randint(min_len, max_len)
        elements = semantic.elements_semantics * length

    return tuple(
        generate_collection_item(ctx, item_semantic, nested_model, None)
        for item_semantic, nested_model in elements
    )


def _generate_invalid_tuple(
    ctx: GenerationContext,
    semantic: TupleSemantic,
    violation: ViolationType,
    target: CollectionTarget | None,
) -> tuple[Any, ...]:
    if violation in (ViolationType.TOO_LESS_ITEMS, ViolationType.TOO_MANY_ITEMS):
        if not semantic.is_variadic:
            raise generation_error(
                "Fixed tuple does not support size violations",
                code="invalid_collection_target",
            )

        min_len, max_len = calculate_valid_collection_range(semantic)
        length = (
            max(0, min_len - 1)
            if violation == ViolationType.TOO_LESS_ITEMS
            else max_len + 1
        )
        return tuple(
            generate_collection_item(ctx, *semantic.elements_semantics[0], None)
            for _ in range(length)
        )

    if semantic.is_variadic:
        min_len, max_len = calculate_valid_collection_range(semantic)
        length = ctx.rng.randint(min_len, max_len)
        elements = semantic.elements_semantics * length
    else:
        elements = semantic.elements_semantics

    if target is None or target.side != "element":
        raise generation_error(
            "Tuple violation requires a planned element target",
            code="missing_collection_target",
        )
    if not 0 <= target.index < len(elements):
        raise generation_error(
            "Tuple target is outside collection",
            code="invalid_collection_target",
            index=target.index,
            size=len(elements),
        )
    violate_idx = target.index
    return tuple(
        generate_collection_item(
            ctx,
            item_semantic,
            nested_model,
            (violation,) if i == violate_idx else None,
        )
        for i, (item_semantic, nested_model) in enumerate(elements)
    )
