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
    "2001:db8.1.1",
    "1200::ABCD::1",
    ":::",
    "2001:db8::1/64",
    "fe80::1%eth0",
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
        existing = prefix.rstrip(":").count(":") + 1 if prefix.rstrip(":") else 0
        remaining = 8 - existing

        if remaining > 0:
            groups = [
                "".join(ctx.rng.choice(AVAILIABLE_CHARS) for _ in range(4))
                for _ in range(remaining)
            ]
            return prefix + ":".join(groups)
        return prefix.rstrip(":")

    if prefix.endswith("::"):
        prefix = prefix[:-2]

    groups = [prefix] if prefix else []
    while len(groups) < 8:
        groups.append("".join(ctx.rng.choice("0123456789abcdef") for _ in range(4)))

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
    groups = address.split(":")

    best_start = best_len = -1
    curr_start = curr_len = -1

    for i, g in enumerate(groups):
        if g == "0000":
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

    if best_len >= 2:
        before = ":".join(groups[:best_start])
        after = ":".join(groups[best_start + best_len :])
        return (
            f"{before}::{after}"
            if before and after
            else f"{before}{after}::"
            if before
            else f"::{after}"
        )

    return address
