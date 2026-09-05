from typing import Any

from ..context import GenerationContext
from ._utils import generate_collection_item

from conformly._internal.resolver.semantics import TupleSemantic
from conformly._internal.types import ViolationType
from conformly.exceptions import PlanningError


def _supports_violation(semantic: Any, violation: ViolationType) -> bool:
    from conformly._internal.planner.field import _define_allowed_violation_types

    try:
        return violation in _define_allowed_violation_types(semantic)
    except PlanningError:
        return False


def generate_value(
    ctx: GenerationContext,
    semantic: TupleSemantic,
    violation: ViolationType | None = None,
) -> tuple[Any, ...]:
    if violation is None:
        return _generate_valid_tuple(ctx, semantic)

    return _generate_invalid_tuple(ctx, semantic, violation)


def _generate_valid_tuple(
    ctx: GenerationContext, semantic: TupleSemantic
) -> tuple[Any, ...]:
    if not semantic.is_variadic:
        elements = semantic.elements_semantics
    else:
        min_len = semantic.length_range.min_length if semantic.length_range else 1
        max_len = semantic.length_range.max_length if semantic.length_range else 3
        length = ctx.rng.randint(min_len or 1, max_len or 3)
        elements = semantic.elements_semantics * length

    return tuple(
        generate_collection_item(ctx, item_semantic, nested_model, None)
        for item_semantic, nested_model in elements
    )


def _generate_invalid_tuple(
    ctx: GenerationContext, semantic: TupleSemantic, violation: ViolationType
) -> tuple[Any, ...]:
    if violation in (ViolationType.TOO_LESS_ITEMS, ViolationType.TOO_MANY_ITEMS):
        if not semantic.is_variadic:
            return _generate_valid_tuple(ctx, semantic)

        min_len = semantic.length_range.min_length if semantic.length_range else 1
        max_len = semantic.length_range.max_length if semantic.length_range else 3
        length = (
            max(0, min_len - 1)
            if violation == ViolationType.TOO_LESS_ITEMS
            else (max_len or 3) + 1
        )
        return tuple(
            generate_collection_item(ctx, *semantic.elements_semantics[0], None)
            for _ in range(length)
        )

    if semantic.is_variadic:
        min_len = semantic.length_range.min_length if semantic.length_range else 1
        max_len = semantic.length_range.max_length if semantic.length_range else 3
        length = ctx.rng.randint(min_len or 1, max_len or 3)
        elements = semantic.elements_semantics * length
    else:
        elements = semantic.elements_semantics

    candidates = [
        i
        for i, (item_semantic, _) in enumerate(elements)
        if _supports_violation(item_semantic, violation)
    ]
    violate_idx = (
        ctx.rng.choice(candidates)
        if candidates
        else ctx.rng.randint(0, len(elements) - 1)
    )
    return tuple(
        generate_collection_item(
            ctx,
            item_semantic,
            nested_model,
            (violation,) if i == violate_idx else None,
        )
        for i, (item_semantic, nested_model) in enumerate(elements)
    )
