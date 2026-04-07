import re
import uuid

import pytest

from conformly.generator.context import GenerationContext
from conformly.generator.types.uuid import generate_value
from conformly.resolver.semantics import UUIDSemantic
from conformly.types import ViolationType

UUID_CANONICAL_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def is_valid_uuid_hex(s: str) -> bool:
    if not UUID_CANONICAL_PATTERN.match(s):
        return False
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


def has_only_hex_and_hyphens(s: str) -> bool:
    return all(c in "0123456789abcdef-" for c in s.lower())


def test_returns_string(ctx: GenerationContext) -> None:
    result = generate_value(ctx, UUIDSemantic(), violation=None)
    assert isinstance(result, str)


def test_valid_format(ctx: GenerationContext) -> None:
    result = generate_value(ctx, UUIDSemantic(), violation=None)
    assert is_valid_uuid_hex(result), f"Got: {result}"


def test_valid_uuid_parseable(ctx: GenerationContext) -> None:
    result = generate_value(ctx, UUIDSemantic(), violation=None)
    parsed = uuid.UUID(result)
    assert parsed.version == 4


@pytest.mark.parametrize(
    "violation",
    [
        ViolationType.TOO_SHORT,
        ViolationType.TOO_LONG,
        ViolationType.WRONG_UUID_FORMAT,
        ViolationType.WRONG_UUID_CHARACTER,
    ],
)
def test_returns_string_for_all_violations(
    ctx: GenerationContext,
    violation: ViolationType,
) -> None:
    result = generate_value(ctx, UUIDSemantic(), violation=violation)
    assert isinstance(result, str)
    assert len(result) > 0


def test_too_short_is_actually_shorter(ctx: GenerationContext) -> None:
    result = generate_value(ctx, UUIDSemantic(), violation=ViolationType.TOO_SHORT)
    assert len(result) < 36, f"Expected <36, got {len(result)}: '{result}'"


def test_too_long_is_actually_longer(ctx: GenerationContext) -> None:
    result = generate_value(ctx, UUIDSemantic(), violation=ViolationType.TOO_LONG)
    assert len(result) > 36, f"Expected >36, got {len(result)}: '{result}'"


def test_invalid_format_not_parseable(ctx: GenerationContext) -> None:
    result = generate_value(
        ctx, UUIDSemantic(), violation=ViolationType.WRONG_UUID_FORMAT
    )
    assert not is_valid_uuid_hex(result), f"Expected invalid, but got valid: '{result}'"


def test_wrong_character_has_non_hex(ctx: GenerationContext) -> None:
    result = generate_value(
        ctx, UUIDSemantic(), violation=ViolationType.WRONG_UUID_CHARACTER
    )
    assert not has_only_hex_and_hyphens(result), f"Expected non-hex char in: '{result}'"


def test_unknown_violation_returns_fallback(ctx: GenerationContext) -> None:
    result = generate_value(
        ctx, UUIDSemantic(), violation=ViolationType.PATTERN_MISMATCH
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_empty_local_not_possible(ctx: GenerationContext) -> None:
    for violation in [
        ViolationType.TOO_SHORT,
        ViolationType.WRONG_UUID_FORMAT,
        ViolationType.WRONG_UUID_CHARACTER,
    ]:
        result = generate_value(ctx, UUIDSemantic(), violation=violation)
        assert result != "", f"Empty result for {violation}"
