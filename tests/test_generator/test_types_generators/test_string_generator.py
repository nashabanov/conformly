import re

import pytest

from conformly.generator.types.string import (
    _generate_invalid_string,
    _generate_valid_string,
    _invert_pattern_string,
    _random_pattern_with_length,
    _random_string_with_length,
    generate_value,
)
from conformly.resolver.semantics import StringSemantic
from conformly.types import FieldKind, LengthRange, ViolationType


def test_random_string_min_only():
    result = _random_string_with_length(10, None)
    assert isinstance(result, str)
    assert 10 <= len(result) <= 60


def test_random_string_max_only():
    result = _random_string_with_length(0, 7)
    assert isinstance(result, str)
    assert 0 <= len(result) <= 7


def test_random_string_min_max():
    result = _random_string_with_length(15, 35)
    assert isinstance(result, str)
    assert 15 <= len(result) <= 35


def test_pattern_no_length_constraints():
    pattern = r"[a-z]{3}"
    result = _random_pattern_with_length(pattern, 0, None)
    assert isinstance(result, str)
    assert re.fullmatch(pattern, result) is not None


def test_invert_pattern_empty_string():
    result = _invert_pattern_string("", r"a*")
    assert result == "x"


def test_simple_pattern():
    s = _random_pattern_with_length(r"[a-z]{5}", 0, None)
    assert re.fullmatch(r"[a-z]{5}", s)
    assert len(s) == 5


def test_with_min_max():
    s = _random_pattern_with_length(r"[a-z]{3,10}", min_len=6, max_len=8)
    assert 6 <= len(s) <= 8
    assert re.fullmatch(r"[a-z]{3,10}", s)


def test_fixed_length_within_bounds():
    s = _random_pattern_with_length(r"\d{4}", min_len=4, max_len=4)
    assert s.isdigit() and len(s) == 4


def test_pattern_always_too_long():
    with pytest.raises(RuntimeError, match="Could not generate"):
        _random_pattern_with_length(r"a{10}", 0, max_len=5)


def test_pattern_always_too_short():
    with pytest.raises(RuntimeError, match="Could not generate"):
        _random_pattern_with_length(r"X", min_len=5, max_len=None)


def test_invalid_regex():
    with pytest.raises(ValueError, match="Invalid or unsupported regex"):
        _random_pattern_with_length(r"[", 0, None)


def test_min_greater_than_max():
    with pytest.raises(ValueError, match="min_len cannot be greater"):
        _random_pattern_with_length(r".*", min_len=10, max_len=5)


def test_flexible_pattern_succeeds():
    s = _random_pattern_with_length(r"[a-z]{1,5}", min_len=3, max_len=4)
    assert 3 <= len(s) <= 4
    assert re.fullmatch(r"[a-z]{1,5}", s)


def test_pattern_empty_string_allowed():
    s = _random_pattern_with_length(r"a*", min_len=0, max_len=0)
    assert s == ""


def test_pattern_with_unicode():
    s = _random_pattern_with_length(r"[а-яё]{3}", 0, None)  # noqa: RUF001
    assert re.fullmatch(r"[а-яё]{3}", s, re.IGNORECASE)  # noqa: RUF001


def test_pattern_with_anchors():
    s = _random_pattern_with_length(r"^[A-Z]{2}\d{3}$", 0, None)
    assert re.fullmatch(r"[A-Z]{2}\d{3}", s)


def test_pattern_max_length_zero():
    with pytest.raises(RuntimeError):
        _random_pattern_with_length(r"[a-z]+", 0, max_len=0)


def test_pattern_min_length_zero():
    s = _random_pattern_with_length(r"[a-z]*", min_len=0, max_len=5)
    assert 0 <= len(s) <= 5
    assert re.fullmatch(r"[a-z]*", s)


def test_pattern_complex_but_compatible():
    s = _random_pattern_with_length(
        r"user_\d{4}@[a-z]{3,5}\.(com|org)", min_len=15, max_len=30
    )
    assert 15 <= len(s) <= 30
    assert re.fullmatch(r"user_\d{4}@[a-z]{3,5}\.(com|org)", s)


def test_generate_valid_no_constraints():
    result = _generate_valid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, None), None)
    )
    assert isinstance(result, str)
    assert 0 <= len(result) <= 50


def test_generate_valid_min_length_only():
    result = _generate_valid_string(
        StringSemantic(FieldKind.STRING, LengthRange(8, None), None)
    )
    assert len(result) >= 8


def test_generate_valid_pattern_only():
    result = _generate_valid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, None), r"[A-Z]{3}")
    )
    assert re.fullmatch(r"[A-Z]{3}", result)


def test_generate_valid_all_constraints():
    result = _generate_valid_string(
        StringSemantic(FieldKind.STRING, LengthRange(6, 10), r"[a-z]{5,12}")
    )
    assert 6 <= len(result) <= 10
    assert re.fullmatch(r"[a-z]{5,12}", result)


def test_generate_invalid_min_length_violation():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(5, None), None),
        ViolationType.TOO_SHORT,
    )
    assert len(result) == 4


def test_generate_invalid_max_length_violation():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, 3), None),
        ViolationType.TOO_LONG,
    )
    assert len(result) == 4


def test_generate_invalid_pattern_violation():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, None), r"[a-z]{3}"),
        ViolationType.PATTERN_MISMATCH,
    )
    assert not re.fullmatch(r"[a-z]{3}", result)


def test_generate_invalid_no_constraints():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, None), None), None
    )
    assert result == "INVALID"


def test_generate_invalid_string_too_short_with_min_0():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, None), None),
        ViolationType.TOO_SHORT,
    )
    assert result == "INVALID"


def test_generate_invalid_string_too_long_with_max_none():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(5, None), None),
        ViolationType.TOO_LONG,
    )
    assert result == "INVALID"


def test_generate_invalid_string_pattern_mismatch_without_pattern():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, None), None),
        ViolationType.PATTERN_MISMATCH,
    )
    assert result == "INVALID"


def test_generate_invalid_precedence_min_over_max():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(5, 10), None),
        ViolationType.TOO_SHORT,
    )
    assert len(result) == 4
    assert not (len(result) >= 5)


def test_generate_invalid_precedence_max_when_no_min():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, 5), None),
        ViolationType.TOO_LONG,
    )
    assert len(result) == 6


def test_generate_invalid_pattern_only():
    result = _generate_invalid_string(
        StringSemantic(FieldKind.STRING, LengthRange(0, None), r"\d{4}"),
        ViolationType.PATTERN_MISMATCH,
    )
    assert not re.fullmatch(r"\d{4}", result)


def test_generate_random_string_valid():
    result = generate_value(
        StringSemantic(FieldKind.STRING, LengthRange(3, None), None), None
    )
    assert len(result) >= 3


def test_generate_random_string_invalid():
    result = generate_value(
        StringSemantic(FieldKind.STRING, LengthRange(0, 2), None),
        ViolationType.TOO_LONG,
    )
    assert len(result) > 2


def test_pattern_with_catastrophic_backtracking_safe():
    with pytest.raises((RuntimeError, ValueError)):
        _random_pattern_with_length(r"(a+)+", 0, 10)
