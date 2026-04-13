import re

import pytest

from conformly._internal.generator.context import GenerationContext
from conformly._internal.generator.types.string import (
    _generate_invalid_string,
    _generate_valid_string,
    _invert_pattern_string,
    _random_pattern_with_length,
    _random_string_with_length,
    generate_value,
)
from conformly._internal.resolver.semantics import StringSemantic
from conformly._internal.types import FieldKind, LengthRange, ViolationType
from conformly.exceptions import GenerationError


def test_random_string_min_only(ctx: GenerationContext) -> None:
    result = _random_string_with_length(ctx, 10, None)
    assert isinstance(result, str)
    assert 10 <= len(result) <= 60


def test_random_string_max_only(ctx: GenerationContext) -> None:
    result = _random_string_with_length(ctx, 0, 7)
    assert isinstance(result, str)
    assert 0 <= len(result) <= 7


def test_random_string_min_max(ctx: GenerationContext) -> None:
    result = _random_string_with_length(ctx, 15, 35)
    assert isinstance(result, str)
    assert 15 <= len(result) <= 35


def test_pattern_no_length_constraints(ctx: GenerationContext) -> None:
    pattern = r"[a-z]{3}"
    result = _random_pattern_with_length(ctx, pattern, 0, None)
    assert isinstance(result, str)
    assert re.fullmatch(pattern, result) is not None


def test_invert_pattern_empty_string() -> None:
    result = _invert_pattern_string("", r"a*")
    assert result == "x"


def test_simple_pattern(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(ctx, r"[a-z]{5}", 0, None)
    assert re.fullmatch(r"[a-z]{5}", s)
    assert len(s) == 5


def test_with_min_max(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(ctx, r"[a-z]{3,10}", min_len=6, max_len=8)
    assert 6 <= len(s) <= 8
    assert re.fullmatch(r"[a-z]{3,10}", s)


def test_fixed_length_within_bounds(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(ctx, r"\d{4}", min_len=4, max_len=4)
    assert s.isdigit() and len(s) == 4


def test_pattern_always_too_long(ctx: GenerationContext) -> None:
    with pytest.raises(GenerationError):
        _random_pattern_with_length(ctx, r"a{10}", 0, max_len=5)


def test_pattern_always_too_short(ctx: GenerationContext) -> None:
    with pytest.raises(GenerationError):
        _random_pattern_with_length(ctx, r"X", min_len=5, max_len=None)


def test_invalid_regex(ctx: GenerationContext) -> None:
    with pytest.raises(GenerationError):
        _random_pattern_with_length(ctx, r"[", 0, None)


def test_min_greater_than_max(ctx: GenerationContext) -> None:
    with pytest.raises(GenerationError):
        _random_pattern_with_length(ctx, r".*", min_len=10, max_len=5)


def test_flexible_pattern_succeeds(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(ctx, r"[a-z]{1,5}", min_len=3, max_len=4)
    assert 3 <= len(s) <= 4
    assert re.fullmatch(r"[a-z]{1,5}", s)


def test_pattern_empty_string_allowed(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(ctx, r"a*", min_len=0, max_len=0)
    assert s == ""


def test_pattern_with_unicode(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(ctx, r"[а-яё]{3}", 0, None)  # noqa: RUF001
    assert re.fullmatch(r"[а-яё]{3}", s, re.IGNORECASE)  # noqa: RUF001


def test_pattern_with_anchors(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(ctx, r"^[A-Z]{2}\d{3}$", 0, None)
    assert re.fullmatch(r"[A-Z]{2}\d{3}", s)


def test_pattern_max_length_zero(ctx: GenerationContext) -> None:
    with pytest.raises(GenerationError):
        _random_pattern_with_length(ctx, r"[a-z]+", 0, max_len=0)


def test_pattern_min_length_zero(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(ctx, r"[a-z]*", min_len=0, max_len=5)
    assert 0 <= len(s) <= 5
    assert re.fullmatch(r"[a-z]*", s)


def test_pattern_complex_but_compatible(ctx: GenerationContext) -> None:
    s = _random_pattern_with_length(
        ctx, r"user_\d{4}@[a-z]{3,5}\.(com|org)", min_len=15, max_len=30
    )
    assert 15 <= len(s) <= 30
    assert re.fullmatch(r"user_\d{4}@[a-z]{3,5}\.(com|org)", s)


def test_generate_valid_no_constraints(ctx: GenerationContext) -> None:
    result = _generate_valid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING, length_range=LengthRange(0, None), pattern=None
        ),
    )
    assert isinstance(result, str)
    assert 0 <= len(result) <= 50


def test_generate_valid_min_length_only(ctx: GenerationContext) -> None:
    result = _generate_valid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(8, None),
            pattern=None,
            has_constraints=True,
        ),
    )
    assert len(result) >= 8


def test_generate_valid_pattern_only(ctx: GenerationContext) -> None:
    result = _generate_valid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(0, None),
            pattern=r"[A-Z]{3}",
            has_constraints=True,
        ),
    )
    assert re.fullmatch(r"[A-Z]{3}", result)


def test_generate_valid_all_constraints(ctx: GenerationContext) -> None:
    result = _generate_valid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(6, 10),
            pattern=r"[a-z]{5,12}",
            has_constraints=True,
        ),
    )
    assert 6 <= len(result) <= 10
    assert re.fullmatch(r"[a-z]{5,12}", result)


def test_generate_invalid_min_length_violation(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(5, None),
            pattern=None,
            has_constraints=True,
        ),
        ViolationType.TOO_SHORT,
    )
    assert len(result) == 4


def test_generate_invalid_max_length_violation(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(0, 3),
            pattern=None,
            has_constraints=True,
        ),
        ViolationType.TOO_LONG,
    )
    assert len(result) == 4


def test_generate_invalid_pattern_violation(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(0, None),
            pattern=r"[a-z]{3}",
            has_constraints=True,
        ),
        ViolationType.PATTERN_MISMATCH,
    )
    assert not re.fullmatch(r"[a-z]{3}", result)


def test_generate_invalid_no_constraints(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING, length_range=LengthRange(0, None), pattern=None
        ),
        None,
    )
    assert result == "INVALID"


def test_generate_invalid_string_too_short_with_min_0(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING, length_range=LengthRange(0, None), pattern=None
        ),
        ViolationType.TOO_SHORT,
    )
    assert result == "INVALID"


def test_generate_invalid_string_too_long_with_max_none(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(5, None),
            pattern=None,
            has_constraints=True,
        ),
        ViolationType.TOO_LONG,
    )
    assert result == "INVALID"


def test_generate_invalid_string_pattern_mismatch_without_pattern(
    ctx: GenerationContext,
) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING, length_range=LengthRange(0, None), pattern=None
        ),
        ViolationType.PATTERN_MISMATCH,
    )
    assert result == "INVALID"


def test_generate_invalid_precedence_min_over_max(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(5, 10),
            pattern=None,
            has_constraints=True,
        ),
        ViolationType.TOO_SHORT,
    )
    assert len(result) == 4
    assert not (len(result) >= 5)


def test_generate_invalid_precedence_max_when_no_min(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(0, 5),
            pattern=None,
            has_constraints=True,
        ),
        ViolationType.TOO_LONG,
    )
    assert len(result) == 6


def test_generate_invalid_pattern_only(ctx: GenerationContext) -> None:
    result = _generate_invalid_string(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(0, None),
            pattern=r"\d{4}",
            has_constraints=True,
        ),
        ViolationType.PATTERN_MISMATCH,
    )
    assert not re.fullmatch(r"\d{4}", result)


def test_generate_random_string_valid(ctx: GenerationContext) -> None:
    result = generate_value(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(3, None),
            pattern=None,
            has_constraints=True,
        ),
        None,
    )
    assert len(result) >= 3


def test_generate_random_string_invalid(ctx: GenerationContext) -> None:
    result = generate_value(
        ctx,
        StringSemantic(
            kind=FieldKind.STRING,
            length_range=LengthRange(0, 2),
            pattern=None,
            has_constraints=True,
        ),
        ViolationType.TOO_LONG,
    )
    assert len(result) > 2


@pytest.mark.xfail
def test_pattern_with_catastrophic_backtracking_safe(ctx: GenerationContext) -> None:
    with pytest.raises(GenerationError):
        _random_pattern_with_length(ctx, r"(a+)+", 0, 10)
