from urllib.parse import ParseResult, urlparse

import pytest

from conformly._internal.generator import GenerationContext
from conformly._internal.generator.types.url import generate_value
from conformly._internal.resolver.semantics.string import StringSemantic
from conformly._internal.types import FieldKind, LengthRange, ViolationType


def parse(url: str) -> ParseResult:
    return urlparse(url)


def is_http(url: str) -> bool:
    p = parse(url)
    return p.scheme in {"http", "https"} and bool(p.netloc)


def is_any_valid(url: str) -> bool:
    p = urlparse(url)

    invalid = (
        not p.scheme
        or not p.netloc
        or " " in url
        or ".." in p.netloc
        or p.netloc.startswith("-")
        or p.netloc.endswith("-")
    )

    return not invalid


@pytest.mark.parametrize("kind", [FieldKind.URL, FieldKind.HTTPURL])
def test_generates_valid_url(kind: FieldKind, ctx: GenerationContext):
    semantic = StringSemantic(
        kind=kind, length_range=LengthRange(0, None), pattern=None
    )

    for _ in range(20):
        url = generate_value(ctx, semantic)
        assert is_any_valid(url), f"Invalid URL: {url!r}"


def test_httpurl_forces_http_scheme(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(0, None), pattern=None
    )

    for _ in range(30):
        assert is_http(generate_value(ctx, semantic))


def test_url_allows_non_http_schemes(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.URL, length_range=LengthRange(0, None), pattern=None
    )

    schemes = {parse(generate_value(ctx, semantic)).scheme for _ in range(80)}

    assert any(s not in {"http", "https"} for s in schemes if s)


@pytest.mark.parametrize("min_len", [0, 10, 20, 50])
def test_respects_min_length(min_len: int, ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(min_len, None), pattern=None
    )

    for _ in range(20):
        assert len(generate_value(ctx, semantic)) >= min_len


@pytest.mark.parametrize("max_len", [25, 50, 100])
def test_respects_max_length(max_len: int, ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(0, max_len), pattern=None
    )

    for _ in range(20):
        assert len(generate_value(ctx, semantic)) <= max_len


def test_respects_range(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(20, 40), pattern=None
    )

    for _ in range(50):
        url = generate_value(ctx, semantic)
        assert 20 <= len(url) <= 40


def test_none_max_length_only_min_bound(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(10, None), pattern=None
    )

    for _ in range(20):
        assert len(generate_value(ctx, semantic)) >= 10


def test_too_short_violation(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(10, None), pattern=None
    )

    for _ in range(20):
        url = generate_value(ctx, semantic, ViolationType.TOO_SHORT)
        assert len(url) < 10


def test_too_long_violation(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(0, 20), pattern=None
    )

    for _ in range(20):
        url = generate_value(ctx, semantic, ViolationType.TOO_LONG)
        assert len(url) > 20


def test_too_long_unbounded(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(0, None), pattern=None
    )

    url = generate_value(ctx, semantic, ViolationType.TOO_LONG)
    assert len(url) > 2000


@pytest.mark.parametrize("kind", [FieldKind.URL, FieldKind.HTTPURL])
def test_wrong_format_is_invalid(kind: FieldKind, ctx: GenerationContext):
    semantic = StringSemantic(
        kind=kind, length_range=LengthRange(0, None), pattern=None
    )

    for _ in range(20):
        url = generate_value(ctx, semantic, ViolationType.WRONG_URL_FORMAT)
        assert not is_any_valid(url)


@pytest.mark.parametrize("kind", [FieldKind.URL, FieldKind.HTTPURL])
def test_wrong_scheme_is_not_http(kind: FieldKind, ctx: GenerationContext):
    semantic = StringSemantic(
        kind=kind, length_range=LengthRange(0, None), pattern=None
    )

    for _ in range(20):
        url = generate_value(ctx, semantic, ViolationType.WRONG_URL_SCHEME)
        p = parse(url)

        assert p.scheme and p.netloc
        assert p.scheme not in {"http", "https"}


def test_httpurl_wrong_scheme_never_http(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(0, None), pattern=None
    )

    for _ in range(30):
        assert not is_http(
            generate_value(ctx, semantic, ViolationType.WRONG_URL_SCHEME)
        )


def test_empty_or_root_path_exists(ctx: GenerationContext):
    semantic = StringSemantic(
        kind=FieldKind.HTTPURL, length_range=LengthRange(0, None), pattern=None
    )

    found = False
    for _ in range(80):
        if parse(generate_value(ctx, semantic)).path in ("", "/"):
            found = True
            break

    assert found
