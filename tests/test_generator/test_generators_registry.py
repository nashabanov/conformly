import pytest

from conformly.generator.protocol import TypeGeneratorProtocol
from conformly.generator.registry import (
    choose_mismatch_kind,
    get_generator,
)
from conformly.generator.types import boolean, enum, float, integer, string
from conformly.types import FieldKind

# ===== TESTS for get_generator() =====


@pytest.mark.parametrize(
    "kind,expected_generator",
    [
        (FieldKind.STRING, string),
        (FieldKind.INTEGER, integer),
        (FieldKind.BOOLEAN, boolean),
        (FieldKind.ENUM, enum),
        (FieldKind.FLOAT, float),
    ],
)
def test_get_generator_returns_correct_implementation(
    kind: FieldKind, expected_generator: TypeGeneratorProtocol
) -> None:
    assert get_generator(kind) is expected_generator


def test_get_generator_raises_on_unknown_kind() -> None:
    with pytest.raises(TypeError):
        get_generator(FieldKind.OBJECT)


# ===== TESTS for get_type_mismatch_generator() =====


@pytest.mark.parametrize("kind", list(FieldKind))
def test_get_type_mismatch_returns_mismatched_generator(kind: FieldKind) -> None:
    assert choose_mismatch_kind(kind) is not kind
