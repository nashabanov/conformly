import string

from ...resolver.semantics import StringSemantic
from ...types import MAX_GENERATION_ATTEMPTS, ViolationType
from ..context import GenerationContext

LOCAL_CHARS = string.ascii_lowercase + string.digits + "._%+-"

DOMAINS = [
    "example.com",
    "example.org",
    "example.net",
    "testmail.com",
    "testmail.org",
    "testmail.net",
    "demomail.com",
    "demomail.org",
    "demomail.net",
    "mockmail.io",
    "fakemail.co",
]

INVALID_FORMATS = [
    "not-an-email",
    "@nodomain.com",
    "no-at-sign",
    "spaces in@email.com",
    "user@.com",
    "user@domain",
    "user@@domain.com",
]

DEFAULT_MIN_LOCAL_LENGTH = 5

MAX_LOCAL_LENGTH = 64

MAX_DOMAIN_LENGTH = 253


def generate_value(
    ctx: GenerationContext, semantic: StringSemantic, violation: ViolationType | None
) -> str:
    return (
        _generate_valid_email(ctx, semantic)
        if not violation
        else _generate_invalid_email(ctx, semantic, violation)
    )


def _generate_valid_email(ctx: GenerationContext, semantic: StringSemantic) -> str:
    min_total = semantic.length_range.min_length
    max_total = semantic.length_range.max_length

    domain = None
    min_local = DEFAULT_MIN_LOCAL_LENGTH
    max_local = MAX_LOCAL_LENGTH

    for _ in range(MAX_GENERATION_ATTEMPTS):
        candidate_domain = ctx.rng.choice(DOMAINS)
        domain_len = len(candidate_domain)

        required_min_local = max(DEFAULT_MIN_LOCAL_LENGTH, min_total - domain_len - 1)
        required_max_local = MAX_LOCAL_LENGTH

        if max_total is not None:
            required_max_local = min(required_max_local, max_total - domain_len - 1)

        if required_min_local <= required_max_local:
            domain = candidate_domain
            min_local = required_min_local
            max_local = required_max_local
            break
    else:
        domain = min(DOMAINS, key=len)
        domain_len = len(domain)

        if max_total is not None:
            max_local = min(MAX_LOCAL_LENGTH, max(1, max_total - domain_len - 1))
            min_local = min(DEFAULT_MIN_LOCAL_LENGTH, max_local)
        else:
            min_local = DEFAULT_MIN_LOCAL_LENGTH
            max_local = DEFAULT_MIN_LOCAL_LENGTH + 10

    local_length = ctx.rng.randint(min_local, max_local)
    local = _generate_local_part(ctx, local_length)

    result = f"{local}@{domain}"

    if max_total is not None and len(result) > max_total:
        max_local_len = max(1, max_total - domain_len - 1)
        local = local[:max_local_len]
        result = f"{local}@{domain}"

    if len(result) < min_total:
        needed = min_total - len(result)
        if max_total is None or len(result) + needed <= max_total:
            padding = "".join(
                ctx.rng.choice(string.ascii_lowercase) for _ in range(needed)
            )
            local = local + padding
            result = f"{local}@{domain}"

    return result


def _generate_invalid_email(
    ctx: GenerationContext, semantic: StringSemantic, violation: ViolationType
) -> str:
    match violation:
        case ViolationType.TOO_SHORT:
            min_total = semantic.length_range.min_length
            if min_total > 1:
                target_len = min_total - 1
                domain = ctx.rng.choice(DOMAINS)
                local_len = max(1, target_len - len(domain) - 1)
                local = _generate_local_part(ctx, local_len)
                return f"{local}@{domain}"
            else:
                return "" if min_total == 0 else "a"

        case ViolationType.TOO_LONG:
            max_total = semantic.length_range.max_length
            if max_total is not None:
                target_len = max_total + 1
                domain = ctx.rng.choice(DOMAINS)
                local_len = max(DEFAULT_MIN_LOCAL_LENGTH, target_len - len(domain) - 1)
                local = _generate_local_part(ctx, min(local_len, MAX_LOCAL_LENGTH))
                return f"{local}@{domain}"
            else:
                local = "a" * (MAX_LOCAL_LENGTH + 10)
                return f"{local}@example.com"

        case ViolationType.NOT_EMAIL:
            return ctx.rng.choice(INVALID_FORMATS)

        case _:
            return "invalid-email"


def _generate_local_part(ctx: GenerationContext, length: int) -> str:
    if length <= 0:
        return ""

    if length == 1:
        return ctx.rng.choice(string.ascii_lowercase + string.digits)

    first = ctx.rng.choice(string.ascii_lowercase + string.digits)

    last = ctx.rng.choice(string.ascii_lowercase + string.digits)

    if length > 2:
        middle_len = length - 2
        middle = "".join(ctx.rng.choice(LOCAL_CHARS) for _ in range(middle_len))
        return f"{first}{middle}{last}"
    else:
        return f"{first}{last}"
