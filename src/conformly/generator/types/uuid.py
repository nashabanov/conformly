import string
import uuid

from ..._internal.types import ViolationType
from ...resolver.semantics import UUIDSemantic
from ..context import GenerationContext

HEX_CHARS = string.hexdigits.lower()
INVALID_CHARS = "!@#$%^&*()ghijklmnopqrstuvwxyz"

INVALID_UUID_TEMPLATES = [
    "not-a-uuid",
    "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx",  # 35 chars
    "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx",  # 37 chars
    "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxy",  # invalid hex
    "xxxxxxxx-xxxx-xxxx-xxxx",  # truncated
    "xxxxxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx",  # wrong segments
    "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx ",  # trailing space
]


def generate_value(
    ctx: GenerationContext, semantic: UUIDSemantic, violation: ViolationType | None
) -> str:
    return (
        _generate_valid_uuid()
        if not violation
        else _generate_invalid_uuid(ctx, violation)
    )


def _generate_valid_uuid() -> str:
    return str(uuid.uuid4())


def _generate_invalid_uuid(ctx: GenerationContext, violation: ViolationType) -> str:
    match violation:
        case ViolationType.TOO_SHORT:
            uid = str(uuid.uuid4())
            chars_to_remove = ctx.rng.randint(1, min(10, len(uid) - 1))
            result = uid[:-chars_to_remove]
            return result if result else "x"

        case ViolationType.TOO_LONG:
            uid = str(uuid.uuid4())
            extra_len = ctx.rng.randint(1, 10)
            extra = "".join(ctx.rng.choice(HEX_CHARS) for _ in range(extra_len))
            return uid + extra

        case ViolationType.WRONG_UUID_FORMAT:
            template = ctx.rng.choice(INVALID_UUID_TEMPLATES)
            if "x" in template:
                return "".join(
                    ctx.rng.choice(HEX_CHARS) if ch == "x" else ch for ch in template
                )
            return template

        case ViolationType.WRONG_UUID_CHARACTER:
            uuid_chars: list[str] = list(str(uuid.uuid4()))
            hex_positions = [i for i, ch in enumerate(uuid_chars) if ch != "-"]
            if hex_positions:
                pos = ctx.rng.choice(hex_positions)
                uuid_chars[pos] = ctx.rng.choice(INVALID_CHARS)
            return "".join(uuid_chars)

        case _:
            return ctx.rng.choice(INVALID_UUID_TEMPLATES)
