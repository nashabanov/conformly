from unittest.mock import Mock, patch

from conformly._internal.generator.types.tuple import generate_value
from conformly._internal.resolver.semantics import TupleSemantic
from conformly._internal.types import ViolationType


def test_generates_fixed_tuple(ctx) -> None:
    semantic = TupleSemantic(elements_semantics=((Mock(), None), (Mock(), None)))
    with patch(
        "conformly._internal.generator.orchestration.generate_field",
        return_value="value",
    ):
        assert generate_value(ctx, semantic) == ("value", "value")


def test_generates_variadic_tuple(ctx) -> None:
    ctx.rng.randint = Mock(return_value=3)
    semantic = TupleSemantic(elements_semantics=((Mock(), None),), is_variadic=True)
    with patch(
        "conformly._internal.generator.orchestration.generate_field",
        return_value="value",
    ):
        assert generate_value(ctx, semantic) == ("value", "value", "value")


def test_applies_element_violation_once(ctx) -> None:
    ctx.rng.randint = Mock(return_value=1)
    semantic = TupleSemantic(elements_semantics=((Mock(), None), (Mock(), None)))
    with patch(
        "conformly._internal.generator.orchestration.generate_field",
        return_value="value",
    ) as generate:
        generate_value(ctx, semantic, ViolationType.TOO_SHORT)
    assert generate.call_args_list[0].args[2] is None
    assert generate.call_args_list[1].args[2] == (ViolationType.TOO_SHORT,)
