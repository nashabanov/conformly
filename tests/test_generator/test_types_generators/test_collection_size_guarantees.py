from itertools import count
from unittest.mock import patch

import pytest
from semantic_factories import numeric_semantic

from conformly._internal.generator.types import (
    dictionaries,
    list as lists,
    tuple as tuples,
)
from conformly._internal.resolver.semantics import (
    BooleanSemantic,
    DictSemantic,
    ListSemantic,
    TupleSemantic,
)
from conformly._internal.types import LengthRange, Range
from conformly.exceptions import GenerationError


@pytest.mark.parametrize(
    "minimum,maximum", [(0, 0), (5, None), (1, 1), (20, 20), (21, 21), (25, 25)]
)
@pytest.mark.parametrize("kind", ["list", "unique", "dict", "tuple"])
def test_generators_fill_declared_size(ctx_deterministic, kind, minimum, maximum):
    bounds = LengthRange(minimum, maximum)
    element = numeric_semantic(valid_range=Range(0, 100_000))
    if kind == "dict":
        module = dictionaries
        semantic = DictSemantic(element, element, length_range=bounds)
    elif kind == "tuple":
        module = tuples
        semantic = TupleSemantic(
            ((element, None),), length_range=bounds, is_variadic=True
        )
    else:
        module = lists
        semantic = ListSemantic(
            element, length_range=bounds, is_unique_items=kind == "unique"
        )
    with patch(f"{module.__name__}.generate_collection_item", side_effect=count()):
        result = module.generate_value(ctx_deterministic, semantic, None)
    assert len(result) >= minimum
    if maximum is not None:
        assert len(result) == maximum
    if kind == "unique":
        assert len(set(result)) == len(result)


@pytest.mark.parametrize("repeats", [25, 99])
@pytest.mark.parametrize("kind", ["list", "dict"])
def test_retries_fill_size_after_more_than_twenty_collisions(
    ctx_deterministic, kind, repeats
):
    if kind == "list":
        module = lists
        semantic = ListSemantic(
            BooleanSemantic(), length_range=LengthRange(2, 2), is_unique_items=True
        )
        candidates = [False] * repeats + [True]
    else:
        module = dictionaries
        semantic = DictSemantic(
            BooleanSemantic(), BooleanSemantic(), length_range=LengthRange(2, 2)
        )
        candidates = [False, "first"] + [False] * (repeats - 1) + [True, "second"]
    with patch(f"{module.__name__}.generate_collection_item", side_effect=candidates):
        result = module.generate_value(ctx_deterministic, semantic, None)
    assert len(result) == 2


@pytest.mark.parametrize("kind", ["list", "dict"])
def test_retry_exhaustion_is_structured(ctx_deterministic, kind):
    if kind == "list":
        module = lists
        semantic = ListSemantic(
            BooleanSemantic(), length_range=LengthRange(2, 2), is_unique_items=True
        )
    else:
        module = dictionaries
        semantic = DictSemantic(
            BooleanSemantic(), BooleanSemantic(), length_range=LengthRange(2, 2)
        )
    with (
        patch(f"{module.__name__}.generate_collection_item", return_value=False),
        pytest.raises(GenerationError) as exc,
    ):
        module.generate_value(ctx_deterministic, semantic, None)
    assert exc.value.context == {
        "code": "collection_retry_exhausted",
        "collection": kind,
        "requested_size": 2,
        "generated_size": 1,
        "attempts": 100,
    }


def test_structural_duplicates_exhaust_retries(ctx_deterministic):
    semantic = ListSemantic(
        BooleanSemantic(), length_range=LengthRange(2, 2), is_unique_items=True
    )
    with (
        patch(
            "conformly._internal.generator.types.list.generate_collection_item",
            side_effect=lambda *args, **kwargs: {"data": {"nested": [1, 2]}},
        ),
        pytest.raises(GenerationError) as exc,
    ):
        lists.generate_value(ctx_deterministic, semantic, None)
    assert exc.value.context["generated_size"] == 1


def test_structural_equality_ignores_dictionary_order(ctx_deterministic):
    semantic = ListSemantic(
        BooleanSemantic(), length_range=LengthRange(2, 2), is_unique_items=True
    )
    candidates = [
        {"a": [1], "b": {"x": 2}},
        {"b": {"x": 2}, "a": [1]},
        {"a": [2], "b": {"x": 2}},
    ]
    with patch(
        "conformly._internal.generator.types.list.generate_collection_item",
        side_effect=candidates,
    ):
        result = lists.generate_value(ctx_deterministic, semantic, None)
    assert result == [candidates[0], candidates[2]]


def test_unhashable_dictionary_keys_exhaust_retries(ctx_deterministic):
    semantic = DictSemantic(
        BooleanSemantic(), BooleanSemantic(), length_range=LengthRange(1, 1)
    )
    with (
        patch(
            "conformly._internal.generator.types.dictionaries.generate_collection_item",
            return_value={},
        ),
        pytest.raises(GenerationError) as exc,
    ):
        dictionaries.generate_value(ctx_deterministic, semantic, None)
    assert exc.value.context["code"] == "collection_retry_exhausted"
    assert exc.value.context["generated_size"] == 0
