import pytest

from conformly._internal.generator.context import GenerationContext
from conformly._internal.generator.types.ipv4 import (
    INVALID_FORMATS,
    _generate_invalid_ipv4,
    _generate_valid_ipv4,
    generate_value,
)
from conformly._internal.types import FieldKind, LengthRange, ViolationType
from conformly.resolver.semantics import StringSemantic


def test_generate_valid_ipv4_format(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    for _ in range(50):
        result = generate_value(ctx, semantic, violation=None)

        parts = result.split(".")
        assert len(parts) == 4, f"Expected 4 octets, got {len(parts)}: {result!r}"

        for part in parts:
            assert part.isdigit(), f"Octet '{part}' is not a digit"
            value = int(part)
            assert 0 <= value <= 255, f"Octet {value} out of range [0, 255]"


def test_generate_valid_ipv4_172_range(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    found_172 = False
    for _ in range(200):
        result = generate_value(ctx, semantic, violation=None)

        if result.startswith("172."):
            found_172 = True
            second_octet = int(result.split(".")[1])
            assert 16 <= second_octet <= 31, (
                f"172.{second_octet}.x.x out of RFC 1918 range"
            )

    assert found_172, "Failed to generate any 172.x.x.x address in 200 attempts"


def test_generate_valid_ipv4_uses_test_ranges(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    found_prefixes = set()
    for _ in range(300):
        result = generate_value(ctx, semantic, violation=None)
        parts = result.split(".")
        prefix = ".".join(parts[:3])
        found_prefixes.add(prefix)

    assert len(found_prefixes) >= 4, (
        f"Expected variety in prefixes, got only: {found_prefixes}"
    )


def test_generate_invalid_ipv4_wrong_format(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    results = set()
    for _ in range(50):
        result = generate_value(ctx, semantic, violation=ViolationType.WRONG_IP_FORMAT)
        results.add(result)
        assert result in INVALID_FORMATS, f"Unexpected invalid format: {result!r}"

    assert len(results) >= 3, (
        f"Expected variety in invalid formats, got only: {results}"
    )


def test_generate_invalid_ipv4_unknown_violation(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_SHORT)

    assert result == "999.999.999.999"


def test_generate_invalid_ipv4_too_long(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_LONG)

    assert result == "999.999.999.999"


def test_generate_invalid_ipv4_too_short_explicit(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_SHORT)

    assert result == "999.999.999.999"


def test_generate_valid_ipv4_direct(ctx: GenerationContext) -> None:
    result = _generate_valid_ipv4(ctx)

    parts = result.split(".")
    assert len(parts) == 4
    assert all(0 <= int(p) <= 255 for p in parts)


def test_generate_invalid_ipv4_direct_wrong_format(ctx: GenerationContext) -> None:
    result = _generate_invalid_ipv4(ctx, ViolationType.WRONG_IP_FORMAT)

    assert result in INVALID_FORMATS


def test_generate_invalid_ipv4_direct_unknown(ctx: GenerationContext) -> None:
    result = _generate_invalid_ipv4(ctx, ViolationType.TOO_LONG)

    assert result == "999.999.999.999"


def test_generated_ipv4_passes_basic_validation(ctx: GenerationContext) -> None:
    import ipaddress

    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    for _ in range(100):
        result = generate_value(ctx, semantic, violation=None)

        try:
            ipaddress.IPv4Address(result)
        except ipaddress.AddressValueError as e:
            pytest.fail(f"Generated invalid IPv4: {result!r} — {e}")


def test_invalid_ipv4_fails_validation(ctx: GenerationContext) -> None:
    import ipaddress

    semantic = StringSemantic(
        kind=FieldKind.IPv4,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    for _ in range(20):
        result = generate_value(ctx, semantic, violation=ViolationType.WRONG_IP_FORMAT)

        with pytest.raises(ipaddress.AddressValueError):
            ipaddress.IPv4Address(result)


def test_invalid_formats_are_invalid() -> None:
    import ipaddress

    for invalid in INVALID_FORMATS:
        with pytest.raises(ipaddress.AddressValueError):
            ipaddress.IPv4Address(invalid)
