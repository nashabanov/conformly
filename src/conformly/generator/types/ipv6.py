from ...resolver.semantics import StringSemantic
from ...types import ViolationType
from ..context import GenerationContext

TEST_PREFIXES = [
    "2001:db8::",
    "2001:0200::",
    "3ffe::",
    "::1",
    "fe80::",
]


INVALID_FORMATS = [
    "2001:db8::1::2",
    "2001:db8:12345::1",
    "2001:db8::g123",
    ":::",
    "gggg::1234",
    "1:2:3:4:5:6:7:8:9",
    "1234::5678::9abc",
    "2001:db8::1/64",
    "::1::",
]

AVAILIABLE_CHARS = "0123456789abcdef"


def generate_value(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType | None = None,
) -> str:
    return (
        _generate_valid_ipv6(ctx)
        if violation is None
        else _generate_invalid_ipv6(ctx, violation)
    )


def _generate_valid_ipv6(ctx: GenerationContext) -> str:
    prefix = ctx.rng.choice(TEST_PREFIXES)

    if prefix == "::1":
        return "::1"

    if "::" in prefix and prefix != "::1":
        parts = prefix.split("::")
        before = [p for p in parts[0].split(":") if p] if parts[0] else []
        after = (
            [p for p in parts[1].split(":") if p] if len(parts) > 1 and parts[1] else []
        )

        existing = len(before) + len(after)
        remaining = 7 - existing

        if remaining > 0:
            groups = [
                "".join(ctx.rng.choice(AVAILIABLE_CHARS) for _ in range(4))
                for _ in range(remaining)
            ]
            if after:
                return (
                    ":".join(before) + "::" + ":".join(groups) + ":" + ":".join(after)
                )
            else:
                return ":".join(before) + "::" + ":".join(groups)
        else:
            return prefix.rstrip(":")

    if prefix.endswith("::"):
        prefix = prefix[:-2]

    groups = [prefix] if prefix else []
    while len(groups) < 8:
        groups.append("".join(ctx.rng.choice(AVAILIABLE_CHARS) for _ in range(4)))

    if ctx.rng.random() < 0.3:
        return _compress_ipv6(":".join(groups))

    return ":".join(groups)


def _generate_invalid_ipv6(
    ctx: GenerationContext,
    violation: ViolationType,
) -> str:
    match violation:
        case ViolationType.WRONG_IP_FORMAT:
            return ctx.rng.choice(INVALID_FORMATS)
        case _:
            return "invalid::ipv6"


def _compress_ipv6(address: str) -> str:
    """Apply RFC 5952 compression: longest run of zeros → ::"""
    if not address:
        return ""

    groups = address.split(":")

    groups = [g.lstrip("0") or "0" for g in groups]

    best_start = best_len = -1
    curr_start = curr_len = -1

    for i, g in enumerate(groups):
        if g == "0":
            if curr_len == -1:
                curr_start, curr_len = i, 1
            else:
                curr_len += 1
        else:
            if curr_len > best_len:
                best_start, best_len = curr_start, curr_len
            curr_len = -1

    if curr_len > best_len:
        best_start, best_len = curr_start, curr_len

    if best_len >= 2 or (len(groups) == 1 and groups[0] == "0"):
        before = ":".join(groups[:best_start])
        after = ":".join(groups[best_start + best_len :])

        if best_len == len(groups):
            return "::"
        elif best_start == 0:
            return f"::{after}"
        elif best_start + best_len == len(groups):
            return f"{before}::"
        else:
            return f"{before}::{after}"

    return ":".join(groups)
