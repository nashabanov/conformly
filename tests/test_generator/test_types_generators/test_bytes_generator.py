import pytest

from conformly._internal.generator.context import create_context
from conformly._internal.generator.types.bytes import generate_value
from conformly._internal.resolver.semantics import BytesSemantic
from conformly._internal.types import LengthRange, ViolationType
from conformly.exceptions import GenerationError


@pytest.mark.parametrize(
    "lower,upper", [(0, 0), (1, 1), (0, 5), (1000, 1000), (1000, None)]
)
def test_valid_bytes_length_and_seed(lower, upper):
    semantic = BytesSemantic(length_range=LengthRange(lower, upper))
    for seed in (0, 1, -1):
        value = generate_value(create_context(seed), semantic, None)
        assert type(value) is bytes
        assert lower <= len(value) <= (upper if upper is not None else lower + 50)
        assert value == generate_value(create_context(seed), semantic, None)


def test_full_byte_domain_is_generated():
    semantic = BytesSemantic(length_range=LengthRange(4096, 4096))
    assert set(generate_value(create_context(0), semantic, None)) == set(range(256))


@pytest.mark.parametrize(
    "violation,length", [(ViolationType.TOO_SHORT, 0), (ViolationType.TOO_LONG, 6)]
)
def test_minimal_length_violations(violation, length):
    semantic = BytesSemantic(length_range=LengthRange(1, 5))
    value = generate_value(create_context(0), semantic, violation)
    assert type(value) is bytes
    assert len(value) == length


@pytest.mark.parametrize(
    "violation",
    [ViolationType.TOO_SHORT, ViolationType.TOO_LONG, ViolationType.PATTERN_MISMATCH],
)
def test_inapplicable_violations_rejected(violation):
    semantic = BytesSemantic(length_range=LengthRange(0, None))
    with pytest.raises(GenerationError):
        generate_value(create_context(0), semantic, violation)
