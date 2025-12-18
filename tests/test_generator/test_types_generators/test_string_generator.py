import re

import pytest

from conformly.generator.types.string import (
    _generate_invalid_string,
    _generate_valid_string,
    _random_pattern_with_length,
    _random_string_with_length,
    generate_value,
    supports,
)
from conformly.specs.field import ConstraintSpec, FieldSpec


def test_random_string_default():
    result = _random_string_with_length(None, None)
    assert isinstance(result, str)
    assert 5 <= len(result) <= 15


def test_random_string_min_only():
    result = _random_string_with_length(10, None)
    assert isinstance(result, str)
    assert 10 <= len(result) <= 60


def test_random_string_max_only():
    result = _random_string_with_length(None, 7)
    assert isinstance(result, str)
    assert 1 <= len(result) <= 7


def test_random_string_min_max():
    result = _random_string_with_length(15, 35)
    assert isinstance(result, str)
    assert 15 <= len(result) <= 35


def test_pattern_no_length_constraints():
    pattern = r"[a-z]{3}"
    result = _random_pattern_with_length(pattern, None, None)
    assert isinstance(result, str)
    assert re.fullmatch(pattern, result) is not None


def test_simple_pattern():
    s = _random_pattern_with_length(r"[a-z]{5}", None, None)
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
        _random_pattern_with_length(r"a{10}", None, max_len=5)


def test_pattern_always_too_short():
    with pytest.raises(RuntimeError, match="Could not generate"):
        _random_pattern_with_length(r"X", min_len=5, max_len=None)


def test_invalid_regex():
    with pytest.raises(ValueError, match="Invalid or unsupported regex"):
        _random_pattern_with_length(r"[", None, None)


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
    s = _random_pattern_with_length(r"[а-яё]{3}", None, None)  # noqa: RUF001
    assert re.fullmatch(r"[а-яё]{3}", s, re.IGNORECASE)  # noqa: RUF001


def test_pattern_with_anchors():
    s = _random_pattern_with_length(r"^[A-Z]{2}\d{3}$", None, None)
    assert re.fullmatch(r"[A-Z]{2}\d{3}", s)


def test_pattern_max_length_zero():
    with pytest.raises(RuntimeError):
        _random_pattern_with_length(r"[a-z]+", None, max_len=0)


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
    result = _generate_valid_string([])
    assert isinstance(result, str)
    assert 5 <= len(result) <= 15


def test_generate_valid_min_length_only():
    constraints = [ConstraintSpec("min_length", 8)]
    result = _generate_valid_string(constraints)
    assert len(result) >= 8


def test_generate_valid_pattern_only():
    constraints = [ConstraintSpec("pattern", r"[A-Z]{3}")]
    result = _generate_valid_string(constraints)
    assert re.fullmatch(r"[A-Z]{3}", result)


def test_generate_valid_all_constraints():
    constraints = [
        ConstraintSpec("min_length", 6),
        ConstraintSpec("max_length", 10),
        ConstraintSpec("pattern", r"[a-z]{5,12}"),
    ]
    result = _generate_valid_string(constraints)
    assert 6 <= len(result) <= 10
    assert re.fullmatch(r"[a-z]{5,12}", result)


def test_generate_invalid_min_length_violation():
    constraints = [ConstraintSpec("min_length", 5)]
    result = _generate_invalid_string(constraints)
    assert len(result) == 4  # 5 - 1


def test_generate_invalid_max_length_violation():
    constraints = [ConstraintSpec("max_length", 3)]
    result = _generate_invalid_string(constraints)
    assert len(result) == 4  # 3 + 1


def test_generate_invalid_pattern_violation():
    constraints = [ConstraintSpec("pattern", r"[a-z]{3}")]
    result = _generate_invalid_string(constraints)
    assert not re.fullmatch(r"[a-z]{3}", result)


def test_generate_invalid_no_constraints():
    result = _generate_invalid_string([])
    assert result == "INVALID"


def test_generate_invalid_precedence_min_over_max():
    constraints = [ConstraintSpec("min_length", 5), ConstraintSpec("max_length", 10)]
    result = _generate_invalid_string(constraints)
    assert len(result) == 4
    assert not (len(result) >= 5)


def test_generate_invalid_precedence_max_when_no_min():
    constraints = [ConstraintSpec("max_length", 5)]
    result = _generate_invalid_string(constraints)
    assert len(result) == 6


def test_generate_invalid_pattern_only():
    constraints = [ConstraintSpec("pattern", r"\d{4}")]
    result = _generate_invalid_string(constraints)
    assert not re.fullmatch(r"\d{4}", result)


def test_generate_random_string_valid():
    constraints = [ConstraintSpec("min_length", 3)]
    result = generate_value(constraints, valid=True)
    assert len(result) >= 3


def test_generate_random_string_invalid():
    constraints = [ConstraintSpec("max_length", 2)]
    result = generate_value(constraints, valid=False)
    assert len(result) > 2


def test_pattern_with_catastrophic_backtracking_safe():
    with pytest.raises((RuntimeError, ValueError)):
        _random_pattern_with_length(r"(a+)+", None, max_len=10)


def test_supports_valid():
    assert supports(FieldSpec(name="test", type=str))


@pytest.mark.parametrize("_type", [int, list, float, dict, bool, set])
def test_supports_invalid(_type):
    assert not supports(FieldSpec(name="test", type=_type))
