import pytest

from conformly._internal.types import ViolationType
from conformly.generator.context import GenerationContext
from conformly.generator.types.enum import _generate_not_allowed_value, generate_value
from conformly.resolver.semantics import EnumSemantic

# ===== TESTS for generate_value() =====


def test_generate_value_valid(ctx: GenerationContext) -> None:
    semantic = EnumSemantic(("active", "inactive", "pending"), True)

    for _ in range(20):
        value = generate_value(ctx, semantic, None)
        assert value in semantic.values


def test_generate_value_invalid(ctx: GenerationContext) -> None:
    semantic = EnumSemantic(("user", "admin"), True)

    for _ in range(20):
        value = generate_value(ctx, semantic, ViolationType.NOT_ALLOWED_VALUE)
        assert value not in semantic.values


def test_generate_value_unsupported_violations(ctx: GenerationContext) -> None:
    semantic = EnumSemantic((1, 2, 3), True)

    with pytest.raises(ValueError):
        generate_value(ctx, semantic, ViolationType.PATTERN_MISMATCH)

    with pytest.raises(ValueError):
        generate_value(ctx, semantic, ViolationType.TYPE_MISMATCH)


def test_generate_value_large_enum_set(ctx: GenerationContext) -> None:
    values = tuple(f"value_{i}" for i in range(1000))
    semantic = EnumSemantic(
        values=values,
        has_constraints=True,
    )

    value = generate_value(ctx, semantic, violation=ViolationType.NOT_ALLOWED_VALUE)
    assert value not in values
    assert isinstance(value, str)


# ===== TESTS for _generate_not_allowed_value() =====


def test_generate_not_allowed_value_string(ctx: GenerationContext) -> None:
    semantic = EnumSemantic(("apple", "cherry", "banana"), True)

    value = _generate_not_allowed_value(ctx, semantic)
    assert value not in semantic.values
    assert isinstance(value, str)


def test_generate_not_allowed_value_int(ctx: GenerationContext) -> None:
    semantic = EnumSemantic((1, 2, 3), True)

    value = _generate_not_allowed_value(ctx, semantic)
    assert value not in semantic.values
    assert isinstance(value, (int, str))


def test_generate_not_allowed_value_float(ctx: GenerationContext) -> None:
    semantic = EnumSemantic((1.0, 2.1, 3.12), True)

    value = _generate_not_allowed_value(ctx, semantic)
    assert value not in semantic.values
    assert isinstance(value, (float, str))


def test_generate_not_allowed_value_bool_full(ctx: GenerationContext) -> None:
    semantic = EnumSemantic((True, False), True)

    value = _generate_not_allowed_value(ctx, semantic)
    assert value not in semantic.values
    assert isinstance(value, str)


def test_generate_not_allowed_value_bool_invert(ctx: GenerationContext) -> None:
    semantic = EnumSemantic((True,), True)

    assert _generate_not_allowed_value(ctx, semantic) is False


def test_generate_not_allowed_value_heterogeneous(ctx: GenerationContext) -> None:
    semantic = EnumSemantic((1, "test", 3.14, True), True)

    value = _generate_not_allowed_value(ctx, semantic)
    assert value not in semantic.values
    assert isinstance(value, str)
