import pytest

from conformly.generator.types.enum import _generate_not_allowed_value, generate_value
from conformly.resolver.semantics import EnumSemantic
from conformly.types import FieldKind, ViolationType

# ===== TESTS for generate_value() =====


def test_generate_value_valid() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, ("active", "inactive", "pending"), True)

    for _ in range(20):
        value = generate_value(semantic, None)
        assert value in semantic.values


def test_generate_value_invalid() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, ("user", "admin"), True)

    for _ in range(20):
        value = generate_value(semantic, ViolationType.NOT_ALLOWED_VALUE)
        assert value not in semantic.values


def test_generate_value_unsupported_violations() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, (1, 2, 3), True)

    with pytest.raises(ValueError):
        generate_value(semantic, ViolationType.PATTERN_MISMATCH)

    with pytest.raises(ValueError):
        generate_value(semantic, ViolationType.TYPE_MISMATCH)


def test_generate_value_large_enum_set() -> None:
    values = tuple(f"value_{i}" for i in range(1000))
    semantic = EnumSemantic(
        kind=FieldKind.ENUM,
        values=values,
        has_constraints=True,
    )

    value = generate_value(semantic, violation=ViolationType.NOT_ALLOWED_VALUE)
    assert value not in values
    assert isinstance(value, str)


# ===== TESTS for _generate_not_allowed_value() =====


def test_generate_not_allowed_value_string() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, ("apple", "cherry", "banana"), True)

    value = _generate_not_allowed_value(semantic)
    assert value not in semantic.values
    assert isinstance(value, str)


def test_generate_not_allowed_value_int() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, (1, 2, 3), True)

    value = _generate_not_allowed_value(semantic)
    assert value not in semantic.values
    assert isinstance(value, (int, str))


def test_generate_not_allowed_value_float() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, (1.0, 2.1, 3.12), True)

    value = _generate_not_allowed_value(semantic)
    assert value not in semantic.values
    assert isinstance(value, (float, str))


def test_generate_not_allowed_value_bool_full() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, (True, False), True)

    value = _generate_not_allowed_value(semantic)
    assert value not in semantic.values
    assert isinstance(value, str)


def test_generate_not_allowed_value_bool_invert() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, (True,), True)

    assert _generate_not_allowed_value(semantic) is False


def test_generate_not_allowed_value_heterogeneous() -> None:
    semantic = EnumSemantic(FieldKind.ENUM, (1, "test", 3.14, True), True)

    value = _generate_not_allowed_value(semantic)
    assert value not in semantic.values
    assert isinstance(value, str)
