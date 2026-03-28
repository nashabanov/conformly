# tests/test_generator/test_types_generators/test_ipvany_generator.py
import ipaddress

import pytest

from conformly.generator.context import GenerationContext
from conformly.generator.types.ipvany import generate_value
from conformly.resolver.semantics import StringSemantic
from conformly.types import FieldKind, LengthRange, ViolationType


def test_generate_ipvany_mixed_types(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPvAny,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    found_ipv4 = False
    found_ipv6 = False

    for _ in range(100):
        result = generate_value(ctx, semantic, violation=None)

        try:
            ipaddress.IPv4Address(result)
            found_ipv4 = True
        except ipaddress.AddressValueError:
            try:
                ipaddress.IPv6Address(result)
                found_ipv6 = True
            except ipaddress.AddressValueError:
                pytest.fail(f"Generated invalid IP: {result!r}")

        if found_ipv4 and found_ipv6:
            break

    assert found_ipv4, "Failed to generate any IPv4 address"
    assert found_ipv6, "Failed to generate any IPv6 address"


def test_generate_ipvany_invalid(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.IPvAny,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.WRONG_IP_FORMAT)

    try:
        ipaddress.IPv4Address(result)
        ipaddress.IPv6Address(result)
        pytest.fail(f"Expected invalid IP, got valid: {result!r}")
    except ipaddress.AddressValueError:
        pass
