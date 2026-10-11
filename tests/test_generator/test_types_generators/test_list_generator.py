from unittest.mock import Mock, patch

import pytest

from conformly._internal.generator.types.list import generate_value
from conformly._internal.planner.model import CollectionTarget
from conformly._internal.resolver.semantics import ListSemantic
from conformly._internal.types import ViolationType


@pytest.fixture
def mock_elem_semantic() -> Mock:
    return Mock()


@pytest.fixture
def list_sem(mock_elem_semantic) -> ListSemantic:
    return ListSemantic(
        element_semantic=mock_elem_semantic,
        element_nested_model=None,
    )


def test_generates_list_of_length_1_to_3(ctx, list_sem) -> None:
    for expected_len in [1, 2, 3]:
        ctx.rng.randint = Mock(return_value=expected_len)
        with patch(
            "conformly._internal.generator.orchestration.generate_semantic_value",
            return_value="v",
        ):
            result = generate_value(ctx, list_sem, None)
            assert len(result) == expected_len


def test_delegates_generation_to_orchestrator(ctx, mock_elem_semantic) -> None:
    ctx.rng.randint = Mock(return_value=3)

    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        return_value="x",
    ) as mock_gen:
        result = generate_value(
            ctx, ListSemantic(element_semantic=mock_elem_semantic), None
        )

        assert len(result) == 3
        assert mock_gen.call_count == 3

        for c in mock_gen.call_args_list:
            assert c.args == (ctx, mock_elem_semantic, None, None)


def test_violation_applied_to_planned_element(ctx, list_sem) -> None:
    ctx.rng.randint = Mock(return_value=3)
    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        side_effect=lambda ctx, semantic, nested, violations: (
            "bad" if violations else "good"
        ),
    ) as mock_gen:
        result = generate_value(
            ctx,
            list_sem,
            ViolationType.TOO_SHORT,
            target=CollectionTarget("element", 1),
        )
    assert result == ["good", "bad", "good"]
    assert sum(c.args[3] is not None for c in mock_gen.call_args_list) == 1


def test_element_violation_requires_planned_target(ctx, list_sem) -> None:
    from conformly.exceptions import GenerationError

    with pytest.raises(GenerationError) as exc:
        generate_value(ctx, list_sem, ViolationType.TOO_SHORT)
    assert exc.value.context["code"] == "missing_collection_target"


def test_nested_model_propagated_directly(ctx, mock_elem_semantic) -> None:
    nested = Mock()
    semantic = ListSemantic(
        element_semantic=mock_elem_semantic, element_nested_model=nested
    )
    ctx.rng.randint = Mock(return_value=1)
    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        return_value={},
    ) as mock_gen:
        generate_value(ctx, semantic, None)
    assert mock_gen.call_args.args == (ctx, mock_elem_semantic, nested, None)


def test_no_violation_passed_when_none(ctx, list_sem) -> None:
    ctx.rng.randint = Mock(return_value=2)

    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        return_value="v",
    ) as mock_gen:
        generate_value(ctx, list_sem, violation=None)

        assert all(c.args[3] is None for c in mock_gen.call_args_list)


def test_unique_items_enforced(ctx, mock_elem_semantic) -> None:
    semantic = ListSemantic(
        element_semantic=mock_elem_semantic,
        is_unique_items=True,
    )

    ctx.rng.randint = Mock(return_value=3)

    values = ["a", "a", "b", "c"]

    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        side_effect=values,
    ):
        result = generate_value(ctx, semantic, None)

        assert len(result) == 3
        assert len(set(result)) == 3


def test_unique_items_with_unhashable_values(ctx, mock_elem_semantic) -> None:
    semantic = ListSemantic(
        element_semantic=mock_elem_semantic,
        is_unique_items=True,
    )

    ctx.rng.randint = Mock(return_value=2)

    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        side_effect=[{"a": 1}, {"a": 1}, {"a": 2}],
    ):
        result = generate_value(ctx, semantic, None)

        assert result == [{"a": 1}, {"a": 2}]


def test_too_less_items_violation(ctx, list_sem) -> None:
    ctx.rng.randint = Mock()

    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        return_value="v",
    ):
        result = generate_value(ctx, list_sem, ViolationType.TOO_LESS_ITEMS)

        assert result == []


def test_too_many_items_violation(ctx, list_sem) -> None:
    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        return_value="v",
    ) as mock_gen:
        result = generate_value(ctx, list_sem, ViolationType.TOO_MANY_ITEMS)

        assert len(result) == 4
        assert mock_gen.call_count == 4


def test_duplicate_violation_preserves_exact_size_two(ctx, mock_elem_semantic) -> None:
    from conformly._internal.types import LengthRange

    semantic = ListSemantic(
        element_semantic=mock_elem_semantic,
        is_unique_items=True,
        length_range=LengthRange(2, 2),
    )
    ctx.rng.randint = Mock(return_value=2)
    with patch(
        "conformly._internal.generator.orchestration.generate_semantic_value",
        return_value={"a": 1},
    ):
        result = generate_value(ctx, semantic, ViolationType.DUPLICATE)
    assert result == [{"a": 1}, {"a": 1}]
