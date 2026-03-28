import ipaddress

import pytest

from conformly.generator.context import GenerationContext
from conformly.generator.types.ipv6 import (
    INVALID_FORMATS,
    TEST_PREFIXES,
    _compress_ipv6,
    _generate_invalid_ipv6,
    _generate_valid_ipv6,
    generate_value,
)
from conformly.resolver.semantics import StringSemantic
from conformly.types import FieldKind, LengthRange, ViolationType


def test_generate_valid_ipv6_format(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    for _ in range(50):
        result = generate_value(ctx, semantic, violation=None)

        try:
            ipaddress.IPv6Address(result)
        except ipaddress.AddressValueError as e:
            pytest.fail(f"Generated invalid IPv6: {result!r} — {e}")


def test_generate_valid_ipv6_localhost(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    found_localhost = False
    for _ in range(200):
        result = generate_value(ctx, semantic, violation=None)

        if result == "::1":
            found_localhost = True
            break

    assert found_localhost, "Failed to generate ::1 in 200 attempts"


def test_generate_valid_ipv6_uses_test_prefixes(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    found_prefixes = set()
    for _ in range(300):
        result = generate_value(ctx, semantic, violation=None)

        for prefix in TEST_PREFIXES:
            if prefix == "::1":
                if result == "::1":
                    found_prefixes.add(prefix)
            elif result.startswith(prefix.rstrip(":")):
                found_prefixes.add(prefix)
                break

    assert len(found_prefixes) >= 3, (
        f"Expected variety in prefixes, got only: {found_prefixes}"
    )


def test_generate_valid_ipv6_compression(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    found_compressed = False
    found_uncompressed = False

    for _ in range(200):
        result = generate_value(ctx, semantic, violation=None)

        if "::" in result:
            found_compressed = True
        else:
            found_uncompressed = True

        if found_compressed and found_uncompressed:
            break

    assert found_compressed, "Failed to generate any compressed IPv6 address"


def test_compress_ipv6_single_run() -> None:
    address = "2001:0db8:0000:0000:0000:0000:0000:0001"
    result = _compress_ipv6(address)

    assert "::" in result
    import ipaddress

    ipaddress.IPv6Address(result)


def test_compress_ipv6_multiple_runs() -> None:
    address = "2001:0000:0000:0001:0000:0000:0000:0001"
    result = _compress_ipv6(address)

    assert result.count("::") == 1


def test_compress_ipv6_no_compression() -> None:
    address = "2001:0db8:0001:0002:0003:0004:0005:0006"
    result = _compress_ipv6(address)

    assert "::" not in result


def test_compress_ipv6_all_zeros() -> None:
    address = "0000:0000:0000:0000:0000:0000:0000:0000"
    result = _compress_ipv6(address)

    assert result == "::"


def test_compress_ipv6_start_with_zeros() -> None:
    address = "0000:0000:0000:0001:0002:0003:0004:0005"
    result = _compress_ipv6(address)

    assert result.startswith("::")


def test_compress_ipv6_end_with_zeros() -> None:
    address = "2001:0db8:0001:0002:0003:0004:0000:0000"
    result = _compress_ipv6(address)

    assert result.endswith("::")


def test_generate_invalid_ipv6_wrong_format(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
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


def test_generate_invalid_ipv6_unknown_violation(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_SHORT)

    assert result == "invalid::ipv6"


def test_generate_invalid_ipv6_too_long(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_LONG)

    assert result == "invalid::ipv6"


def test_generate_valid_ipv6_direct(ctx: GenerationContext) -> None:
    result = _generate_valid_ipv6(ctx)

    try:
        ipaddress.IPv6Address(result)
    except ipaddress.AddressValueError as e:
        pytest.fail(f"Generated invalid IPv6: {result!r} — {e}")


def test_generate_invalid_ipv6_direct_wrong_format(ctx: GenerationContext) -> None:
    result = _generate_invalid_ipv6(ctx, ViolationType.WRONG_IP_FORMAT)

    assert result in INVALID_FORMATS


def test_generate_invalid_ipv6_direct_unknown(ctx: GenerationContext) -> None:
    result = _generate_invalid_ipv6(ctx, ViolationType.TOO_LONG)

    assert result == "invalid::ipv6"


def test_generated_ipv6_passes_basic_validation(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    for _ in range(100):
        result = generate_value(ctx, semantic, violation=None)

        try:
            ipaddress.IPv6Address(result)
        except ipaddress.AddressValueError as e:
            pytest.fail(f"Generated invalid IPv6: {result!r} — {e}")


def test_invalid_ipv6_fails_validation(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPv6,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    for _ in range(20):
        result = generate_value(ctx, semantic, violation=ViolationType.WRONG_IP_FORMAT)

        with pytest.raises(ipaddress.AddressValueError):
            ipaddress.IPv6Address(result)


@pytest.mark.parametrize("invalid_format", INVALID_FORMATS)
def test_invalid_formats_are_invalid(invalid_format: str) -> None:
    with pytest.raises(ipaddress.AddressValueError):
        ipaddress.IPv6Address(invalid_format)


def test_compress_ipv6_empty_string() -> None:
    result = _compress_ipv6("")
    assert result == ""


def test_compress_ipv6_single_group() -> None:
    result = _compress_ipv6("0000")
    assert result == "::"


def test_compress_ipv6_no_zeros() -> None:
    address = "2001:0db8:0001:0002:0003:0004:0005:0006"
    result = _compress_ipv6(address)

    assert "::" not in result
