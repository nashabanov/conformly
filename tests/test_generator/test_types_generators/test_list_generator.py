from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from conformly._internal.generator.types.list import generate_value
from conformly._internal.resolver.semantics import ListSemantic
from conformly._internal.types import UNSET, ViolationType

if TYPE_CHECKING:
    from conformly._internal.resolver import ResolvedField


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
            "conformly._internal.generator.orchestration.generate_field",
            return_value="v",
        ):
            result = generate_value(ctx, list_sem, None)
            assert len(result) == expected_len


def test_delegates_generation_to_orchestrator(ctx, mock_elem_semantic) -> None:
    ctx.rng.randint = Mock(return_value=3)

    with patch(
        "conformly._internal.generator.orchestration.generate_field", return_value="x"
    ) as mock_gen:
        result = generate_value(
            ctx, ListSemantic(element_semantic=mock_elem_semantic), None
        )

        assert len(result) == 3
        assert mock_gen.call_count == 3

        for c in mock_gen.call_args_list:
            _, field, _ = c.args
            assert field.semantic is mock_elem_semantic
            assert field.nullable is False
            assert field.default is UNSET


def test_violation_applied_to_single_random_element(ctx, list_sem) -> None:
    ctx.rng.randint = Mock(side_effect=[3, 1])

    with patch(
        "conformly._internal.generator.orchestration.generate_field", return_value="v"
    ) as mock_gen:
        generate_value(ctx, list_sem, ViolationType.TOO_SHORT)

        calls = mock_gen.call_args_list
        assert len(calls) == 3

        assert calls[0].args[2] is None
        assert calls[1].args[2] == (ViolationType.TOO_SHORT,)
        assert calls[2].args[2] is None


def test_missing_field_fallback_returns_valid_element(ctx, list_sem) -> None:
    ctx.rng.randint = Mock(side_effect=[2, 0])

    with patch(
        "conformly._internal.generator.orchestration.generate_field"
    ) as mock_gen:
        mock_gen.side_effect = ["valid", "valid2"]

        result = generate_value(ctx, list_sem, ViolationType.MISSING_FIELD)

        assert result == ["valid", "valid2"]
        assert mock_gen.call_count == 2


def test_nested_model_propagated_to_synthetic_field(ctx, mock_elem_semantic) -> None:
    nested_model_mock = Mock()
    semantic = ListSemantic(
        element_semantic=mock_elem_semantic,
        element_nested_model=nested_model_mock,
    )
    ctx.rng.randint = Mock(return_value=1)

    with patch(
        "conformly._internal.generator.orchestration.generate_field", return_value={}
    ) as mock_gen:
        generate_value(ctx, semantic, None)

        synthetic_field: ResolvedField = mock_gen.call_args_list[0].args[1]
        assert synthetic_field.nested_model is nested_model_mock
        assert synthetic_field.semantic is mock_elem_semantic


def test_no_violation_passed_when_none(ctx, list_sem) -> None:
    ctx.rng.randint = Mock(return_value=2)

    with patch(
        "conformly._internal.generator.orchestration.generate_field", return_value="v"
    ) as mock_gen:
        generate_value(ctx, list_sem, violation=None)

        assert all(c.args[2] is None for c in mock_gen.call_args_list)


def test_unique_items_enforced(ctx, mock_elem_semantic) -> None:
    semantic = ListSemantic(
        element_semantic=mock_elem_semantic,
        is_unique_items=True,
    )

    ctx.rng.randint = Mock(return_value=3)

    values = ["a", "a", "b", "c"]

    with patch(
        "conformly._internal.generator.orchestration.generate_field",
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
        "conformly._internal.generator.orchestration.generate_field",
        return_value={"a": 1},
    ):
        result = generate_value(ctx, semantic, None)

        assert len(result) == 2


def test_too_less_items_violation(ctx, list_sem) -> None:
    ctx.rng.randint = Mock()

    with patch(
        "conformly._internal.generator.orchestration.generate_field",
        return_value="v",
    ):
        result = generate_value(ctx, list_sem, ViolationType.TOO_LESS_ITEMS)

        assert result == []


def test_too_many_items_violation(ctx, list_sem) -> None:
    with patch(
        "conformly._internal.generator.orchestration.generate_field",
        return_value="v",
    ) as mock_gen:
        result = generate_value(ctx, list_sem, ViolationType.TOO_MANY_ITEMS)

        assert len(result) == 4
        assert mock_gen.call_count == 4


def test_duplicate_violation_creates_duplicate(ctx, mock_elem_semantic) -> None:
    semantic = ListSemantic(
        element_semantic=mock_elem_semantic,
        is_unique_items=True,
    )

    ctx.rng.randint = Mock(side_effect=[2, 0])

    with patch(
        "conformly._internal.generator.orchestration.generate_field",
        side_effect=["a", "b"],
    ):
        result = generate_value(ctx, semantic, ViolationType.DUPLICATE)

        assert len(result) == 3
        assert len(set(result)) < len(result)


def test_duplicate_violation_on_empty_base(ctx, list_sem) -> None:
    with (
        patch(
            "conformly._internal.generator.types.list._generate_valid_list",
            return_value=[],
        ),
        patch(
            "conformly._internal.generator.orchestration.generate_field",
            return_value="x",
        ),
    ):
        result = generate_value(ctx, list_sem, ViolationType.DUPLICATE)

        assert result == ["x", "x"]


def test_non_collection_violation_still_targets_single_item(ctx, list_sem) -> None:
    ctx.rng.randint = Mock(side_effect=[3, 2])

    with patch(
        "conformly._internal.generator.orchestration.generate_field",
        return_value="v",
    ) as mock_gen:
        generate_value(ctx, list_sem, ViolationType.TOO_SHORT)

        calls = mock_gen.call_args_list

        assert calls[0].args[2] is None
        assert calls[1].args[2] is None
        assert calls[2].args[2] == (ViolationType.TOO_SHORT,)
