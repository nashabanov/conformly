from ..context import GenerationContext

from conformly._internal.resolver.semantics import StringSemantic
from conformly._internal.types import FieldKind, ViolationType

HTTP_SCHEMES = ["http", "https"]
NON_HTTP_SCHEMES = ["ftp", "ftps", "ws", "wss", "file"]
VALID_SCHEMES = HTTP_SCHEMES + NON_HTTP_SCHEMES

VALID_DOMAINS = [
    "example.com",
    "test.org",
    "my-site.net",
    "sub.domain.io",
]

VALID_PATHS = [
    "",
    "/",
    "/api",
    "/api/v1/resource",
    "/users/123",
]

INVALID_URLS = [
    "http:///example.com",
    "://example.com",
    "http://",
    "example.com",
    "http://exa mple.com",
    "http://.com",
    "http://?query",
]


def generate_value(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType | None = None,
) -> str:
    return (
        _generate_valid_url(ctx, semantic.kind)
        if violation is None
        else _generate_invalid_url(ctx, violation)
    )


def _generate_valid_url(ctx: GenerationContext, kind: FieldKind) -> str:
    if kind == FieldKind.HTTPURL:
        scheme = ctx.rng.choice(HTTP_SCHEMES)
    else:
        scheme = ctx.rng.choice(VALID_SCHEMES)

    domain = ctx.rng.choice(VALID_DOMAINS)
    path = ctx.rng.choice(VALID_PATHS)

    return f"{scheme}://{domain}{path}"


def _generate_invalid_url(ctx: GenerationContext, violation: ViolationType) -> str:
    match violation:
        case ViolationType.WRONG_URL_FORMAT:
            scheme = ctx.rng.choice(NON_HTTP_SCHEMES)
            domain = ctx.rng.choice(VALID_DOMAINS)
            path = ctx.rng.choice(VALID_PATHS)
            return f"{scheme}://{domain}{path}"

        case ViolationType.WRONG_URL_SCHEME:
            return ctx.rng.choice(INVALID_URLS)

        case _:
            return "not-a-url"
