import string

from ..context import GenerationContext

from conformly._internal.resolver.semantics import StringSemantic
from conformly._internal.types import FieldKind, ViolationType

HTTP_SCHEMES = ["http", "https"]
ALL_SCHEMES = [*HTTP_SCHEMES, "ftp", "ftps", "ws", "wss", "file"]

DOMAINS = [
    "example.com",
    "test.org",
    "my-site.net",
    "api.example.com",
]

PATH_CHARS = string.ascii_lowercase + string.digits + "/._-~?&=#%"

INVALID_SCHEMES = ["custom", "invalid", "foo", "bar"]


def generate_value(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType | None = None,
) -> str:
    if violation is None:
        return _generate_valid_url(ctx, semantic)

    return _generate_invalid_url(ctx, semantic, violation)


def _generate_valid_url(ctx: GenerationContext, semantic: StringSemantic) -> str:
    min_len = semantic.length_range.min_length
    max_len = semantic.length_range.max_length

    schemes = HTTP_SCHEMES if semantic.kind == FieldKind.HTTPURL else ALL_SCHEMES

    for _ in range(50):
        scheme = ctx.rng.choice(schemes)
        domain = ctx.rng.choice(DOMAINS)

        base = f"{scheme}://{domain}"
        base_len = len(base)

        min_path = max(0, min_len - base_len)

        max_path = 2048 if max_len is None else max(0, max_len - base_len)

        if min_path > max_path:
            continue

        path_len = ctx.rng.randint(min_path, max_path)
        path = _gen_path(ctx, path_len)

        return base + path

    scheme = schemes[0]
    domain = DOMAINS[0]
    return f"{scheme}://{domain}"


def _gen_path(ctx: GenerationContext, length: int) -> str:
    if length <= 0:
        return ""
    if length == 1:
        return "/"

    chars = ["/"]
    while len(chars) < length:
        chars.append(ctx.rng.choice(PATH_CHARS))

    return "".join(chars[:length])


def _generate_invalid_url(
    ctx: GenerationContext,
    semantic: StringSemantic,
    violation: ViolationType,
) -> str:
    min_len = semantic.length_range.min_length
    max_len = semantic.length_range.max_length

    if violation == ViolationType.TOO_SHORT:
        if min_len <= 1:
            return ""
        return "x" * (min_len - 1)

    if violation == ViolationType.TOO_LONG:
        target = (max_len or 2048) + 10
        return "http://example.com/" + "a" * target

    if violation == ViolationType.WRONG_URL_FORMAT:
        return ctx.rng.choice(
            [
                "",
                "   ",
                "not-a-url",
                "http:/broken",
                "http:// bad.com",
                "://missing.scheme.com",
            ]
        )

    if violation == ViolationType.WRONG_URL_SCHEME:
        scheme = ctx.rng.choice(INVALID_SCHEMES)
        return f"{scheme}://example.com"

    return "not-a-url"
