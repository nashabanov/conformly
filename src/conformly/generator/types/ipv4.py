from ...resolver.semantics import StringSemantic
from ...types import ViolationType
from ..context import GenerationContext

TEST_RANGES = [
    ("192.0.2", 1, 254),
    ("198.51.100", 1, 254),
    ("203.0.113", 1, 254),
    ("127.0.0", 1, 254),
    ("10.0.0", 1, 254),
    ("172.16.0", 0, 255),
    ("192.168.0", 1, 254),
]

INVALID_FORMATS = [
    "256.1.1.1",
    "1.2.3",
    "1.2.3.4.5",
    "192.168.1.256",
    "192.168.01.1",
    "192.168.1.1.",
    ".192.168.1.1",
    "192.168.1.-1",
    "192.168.1.abc",
]


def generate_value(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType | None = None,
) -> str:
    return (
        _generate_valid_ipv4(ctx)
        if violation is None
        else _generate_invalid_ipv4(ctx, violation)
    )


def _generate_valid_ipv4(ctx: GenerationContext) -> str:
    prefix, min_last, max_last = ctx.rng.choice(TEST_RANGES)

    if prefix.startswith("172.16"):
        second = ctx.rng.randint(16, 32)
        prefix = f"172.{second}.0"

    last = ctx.rng.randint(min_last, max_last)
    return f"{prefix}.{last}"


def _generate_invalid_ipv4(
    ctx: GenerationContext,
    violation: ViolationType,
) -> str:
    match violation:
        case ViolationType.WRONG_IP_FORMAT:
            return ctx.rng.choice(INVALID_FORMATS)
        case _:
            return "999.999.999.999"
