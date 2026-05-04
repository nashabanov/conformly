from unittest.mock import Mock, patch

import pytest

from conformly._internal.generator.types.dictionaries import generate_value
from conformly._internal.resolver.semantics import DictSemantic
from conformly._internal.types import ViolationType

DICT_MODULE = "conformly._internal.generator.types.dictionaries"


@pytest.fixture
def ctx() -> Mock:
    mock_ctx = Mock()
    mock_ctx.rng = Mock()
    return mock_ctx


@pytest.fixture
def key_sem() -> Mock:
    return Mock()


@pytest.fixture
def value_sem() -> Mock:
    return Mock()


@pytest.fixture
def dict_sem(key_sem: Mock, value_sem: Mock) -> DictSemantic:
    return DictSemantic(
        key_semantic=key_sem,
        value_semantic=value_sem,
        value_nested_model=None,
    )


def test_generates_dict_of_valid_length(ctx: Mock, dict_sem: DictSemantic) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 3)):
        ctx.rng.randint = Mock(return_value=2)
        with patch(
            f"{DICT_MODULE}.generate_collection_item",
            side_effect=["k1", "v1", "k2", "v2"],
        ):
            result = generate_value(ctx, dict_sem, None)
            assert len(result) == 2
            assert result == {"k1": "v1", "k2": "v2"}


def test_delegates_to_collection_item_generator(
    ctx: Mock, key_sem: Mock, value_sem: Mock
) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 1)):
        ctx.rng.randint = Mock(return_value=1)
        with patch(
            f"{DICT_MODULE}.generate_collection_item", return_value="item"
        ) as mock_gen:
            generate_value(ctx, DictSemantic(key_sem, value_sem, None), None)

            assert mock_gen.call_count == 2

            key_call = mock_gen.call_args_list[0].args
            assert key_call[0] is ctx
            assert key_call[1] is key_sem
            assert key_call[2] is None
            assert key_call[3] is None

            val_call = mock_gen.call_args_list[1].args
            assert val_call[0] is ctx
            assert val_call[1] is value_sem
            assert val_call[2] is None
            assert val_call[3] is None


def test_no_violation_passed_when_none(ctx: Mock, dict_sem: DictSemantic) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 2)):
        ctx.rng.randint = Mock(return_value=2)
        with patch(
            f"{DICT_MODULE}.generate_collection_item",
            side_effect=["k1", "v1", "k2", "v2"],
        ) as mock_gen:
            generate_value(ctx, dict_sem, violation=None)
            assert all(c.args[3] is None for c in mock_gen.call_args_list)


def test_too_less_items_violation(ctx: Mock, dict_sem: DictSemantic) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(3, 5)):
        ctx.rng.randint = Mock(side_effect=RuntimeError("Should not be called"))
        with patch(
            f"{DICT_MODULE}.generate_collection_item",
            side_effect=["k1", "v1", "k2", "v2"],
        ) as mock_gen:
            result = generate_value(ctx, dict_sem, ViolationType.TOO_LESS_ITEMS)
            assert len(result) == 2
            assert mock_gen.call_count == 4


def test_too_less_items_violation_with_min_zero(
    ctx: Mock, dict_sem: DictSemantic
) -> None:
    with (
        patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(0, 2)),
        patch(f"{DICT_MODULE}.generate_collection_item", return_value="v") as mock_gen,
    ):
        result = generate_value(ctx, dict_sem, ViolationType.TOO_LESS_ITEMS)
        assert result == {}
        assert mock_gen.call_count == 0


def test_too_many_items_violation(ctx: Mock, dict_sem: DictSemantic) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 3)):
        side_effect_vals = [f"k{i}" for i in range(4)] + [f"v{i}" for i in range(4)]
        with patch(
            f"{DICT_MODULE}.generate_collection_item", side_effect=side_effect_vals
        ) as mock_gen:
            result = generate_value(ctx, dict_sem, ViolationType.TOO_MANY_ITEMS)
            assert len(result) == 4
            assert mock_gen.call_count == 8


def test_violation_applied_to_key(ctx: Mock, dict_sem: DictSemantic) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 3)):
        ctx.rng.randint = Mock(return_value=2)
        ctx.rng.choice = Mock(return_value=True)
        with patch(
            f"{DICT_MODULE}.generate_collection_item",
            side_effect=["k1", "v1", "k2", "v2"],
        ) as mock_gen:
            generate_value(ctx, dict_sem, ViolationType.TOO_SHORT)

            calls = mock_gen.call_args_list
            assert len(calls) == 4
            assert calls[0].args[3] == (ViolationType.TOO_SHORT,)
            assert calls[1].args[3] is None
            assert calls[2].args[3] is None
            assert calls[3].args[3] is None


def test_violation_applied_to_value(ctx: Mock, dict_sem: DictSemantic) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 3)):
        ctx.rng.randint = Mock(return_value=2)
        ctx.rng.choice = Mock(return_value=False)
        with patch(
            f"{DICT_MODULE}.generate_collection_item",
            side_effect=["k1", "v1", "k2", "v2"],
        ) as mock_gen:
            generate_value(ctx, dict_sem, ViolationType.TOO_SHORT)

            calls = mock_gen.call_args_list
            assert len(calls) == 4
            assert calls[0].args[3] is None
            assert calls[1].args[3] == (ViolationType.TOO_SHORT,)
            assert calls[2].args[3] is None
            assert calls[3].args[3] is None


def test_skips_unhashable_keys(ctx: Mock, dict_sem: DictSemantic) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 2)):
        ctx.rng.randint = Mock(return_value=2)
        with (
            patch(f"{DICT_MODULE}.is_hashable", side_effect=[False, True, True]),
            patch(
                f"{DICT_MODULE}.generate_collection_item",
                side_effect=["bad", "k1", "v1", "k2", "v2"],
            ) as mock_gen,
        ):
            result = generate_value(ctx, dict_sem, None)
            assert len(result) == 2
            assert mock_gen.call_count == 5


def test_skips_duplicate_keys(ctx: Mock, dict_sem: DictSemantic) -> None:
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 2)):
        ctx.rng.randint = Mock(return_value=2)
        with (
            patch(f"{DICT_MODULE}.is_hashable", return_value=True),
            patch(
                f"{DICT_MODULE}.generate_collection_item",
                side_effect=["k1", "v1", "k1", "k2", "v2"],
            ) as mock_gen,
        ):
            result = generate_value(ctx, dict_sem, None)
            assert len(result) == 2
            assert result == {"k1": "v1", "k2": "v2"}
            assert mock_gen.call_count == 5


def test_nested_model_propagated_to_value(
    ctx: Mock, key_sem: Mock, value_sem: Mock
) -> None:
    nested_model_mock = Mock()
    semantic = DictSemantic(
        key_semantic=key_sem,
        value_semantic=value_sem,
        value_nested_model=nested_model_mock,
    )
    with patch(f"{DICT_MODULE}.calculate_valid_collection_range", return_value=(1, 1)):
        ctx.rng.randint = Mock(return_value=1)
        with patch(
            f"{DICT_MODULE}.generate_collection_item",
            side_effect=["valid_key", "valid_value"],
        ) as mock_gen:
            generate_value(ctx, semantic, None)

            val_call_args = mock_gen.call_args_list[1].args
            assert val_call_args[1] is value_sem
            assert val_call_args[2] is nested_model_mock
            assert val_call_args[3] is None
