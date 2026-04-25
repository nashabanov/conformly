from typing import Any

from ..context import GenerationContext

from conformly._internal.resolver import ResolvedModel
from conformly._internal.resolver.semantics import FieldSemantics, ListSemantic
from conformly._internal.types import UNSET, ViolationType


def generate_value(
    ctx: GenerationContext, semantic: ListSemantic, violation: ViolationType | None
) -> list[Any]:
    return (
        _generate_valid_list(ctx, semantic)
        if not violation
        else _generate_invalid_list(ctx, semantic, violation)
    )


def _generate_valid_list(ctx: GenerationContext, semantic: ListSemantic) -> list[Any]:
    min_len, max_len = _calculate_valid_range(semantic)

    length = ctx.rng.randint(min_len, max_len)

    result: list[Any] = []

    if not semantic.is_unique_items:
        for _ in range(length):
            item = _generate_list_item(
                ctx, semantic.element_semantic, semantic.element_nested_model, None
            )
            result.append(item)

    seen = set()
    max_attempts = 20

    while len(result) < length and max_attempts > 0:
        item = _generate_list_item(
            ctx, semantic.element_semantic, semantic.element_nested_model, None
        )

        if not _is_hashable(item):
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
    min_len, max_len = _calculate_valid_range(semantic)

    result: list[Any] = []

    match violation:
        case ViolationType.TOO_LESS_ITEMS:
            length = max(0, min_len - 1)
            return [
                _generate_list_item(
                    ctx, semantic.element_semantic, semantic.element_nested_model, None
                )
                for _ in range(length)
            ]

        case ViolationType.TOO_MANY_ITEMS:
            length = max_len + 1
            return [
                _generate_list_item(
                    ctx, semantic.element_semantic, semantic.element_nested_model, None
                )
                for _ in range(length)
            ]

        case ViolationType.DUPLICATE:
            base = _generate_valid_list(ctx, semantic)

            if not base:
                item = _generate_list_item(
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
                item = _generate_list_item(
                    ctx,
                    semantic.element_semantic,
                    semantic.element_nested_model,
                    item_violation,
                )
                result.append(item)

    return result


def _generate_list_item(
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


def _calculate_valid_range(semantic: ListSemantic) -> tuple[int, int]:
    if semantic.length_range is None:
        min_len = 1
        max_len = 3
    else:
        min_len = semantic.length_range.min_length or 1
        max_len = semantic.length_range.max_length or 3

    if min_len == 0:
        min_len = 1

    return min_len, max_len


def _is_hashable(value: Any) -> bool:
    try:
        hash(value)
        return True
    except TypeError:
        return False
