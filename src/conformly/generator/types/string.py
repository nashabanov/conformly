from collections.abc import Sequence
import random
import re
import string

import rstr

from conformly.constraints import Constraint, MaxLength, MinLength, Pattern
from conformly.specs import FieldSpec


def supports(field: FieldSpec) -> bool:
    return field.type is str


def generate_value(constraints: Sequence[Constraint], valid: bool) -> str:
    return (
        _generate_valid_string(constraints)
        if valid
        else _generate_invalid_string(constraints)
    )


def _generate_valid_string(constraints: Sequence[Constraint]) -> str:
    min_len = _get_min_length(constraints)
    max_len = _get_max_length(constraints)
    pattern = _get_pattern(constraints)

    if pattern:
        if max_len is None and min_len is None:
            return rstr.xeger(pattern)
        else:
            return _random_pattern_with_length(pattern, min_len, max_len)

    return _random_string_with_length(min_len, max_len)


def _generate_invalid_string(constraints: Sequence[Constraint]) -> str:
    if min_length := _get_min_length(constraints):
        return _random_string_fixed_length(min_length - 1)

    if max_length := _get_max_length(constraints):
        return _random_string_fixed_length(max_length + 1)

    if pattern := _get_pattern(constraints):
        valid_example = rstr.xeger(pattern)
        return _invert_pattern_string(valid_example, pattern)

    return "INVALID"


def _get_min_length(constraints: Sequence[Constraint]) -> int | None:
    for c in constraints:
        if isinstance(c, MinLength):
            return c.value
    return None


def _get_max_length(constraints: Sequence[Constraint]) -> int | None:
    for c in constraints:
        if isinstance(c, MaxLength):
            return c.value
    return None


def _get_pattern(constraints: Sequence[Constraint]) -> str | None:
    for c in constraints:
        if isinstance(c, Pattern):
            return c.regex
    return None


def _random_string_with_length(min_len: int | None, max_len: int | None) -> str:
    if min_len and max_len is None:
        length = random.randint(min_len, min_len + 50)
        return rstr.rstr(string.ascii_letters + string.digits, length)

    if max_len and min_len is None:
        length = random.randint(1, max_len)
        return rstr.rstr(string.ascii_letters + string.digits, length)

    if min_len and max_len:
        length = random.randint(min_len, max_len)
        return rstr.rstr(string.ascii_letters + string.digits, length)

    length = random.randint(5, 15)
    return rstr.rstr(string.ascii_letters + string.digits, length)


def _random_string_fixed_length(length: int) -> str:
    if length < 0:
        raise ValueError("Length must be non-negative")
    if length == 0:
        return ""
    return rstr.rstr(string.ascii_letters + string.digits, length)


def _random_pattern_with_length(
    pattern: str, min_len: int | None, max_len: int | None
) -> str:
    if min_len is not None and max_len is not None and min_len > max_len:
        raise ValueError("min_len cannot be greater than max_len")
    if min_len is not None and min_len < 0:
        raise ValueError("min_len must be non-negative")
    if max_len is not None and max_len < 0:
        raise ValueError("max_len must be non-negative")

    compiled = None
    try:
        compiled = re.compile(pattern)
    except re.error as e:
        raise ValueError(f"Invalid or unsupported regex pattern: {pattern!r}") from e

    if min_len == 0 and compiled.fullmatch(""):
        return ""

    if min_len == 0 and max_len == 0:
        empty_ok = compiled.fullmatch("")
        if empty_ok:
            return ""
        else:
            raise RuntimeError(
                f"Pattern {pattern!r} does not allow empty string, "
                "but min_len=max_len=0"
            )
    for _ in range(20):
        try:
            candidate = rstr.xeger(pattern)
        except Exception as e:
            raise ValueError(f"Invalid or unsupported regex pattern: {pattern}") from e

        if len(candidate) > 1000:
            continue

        n = len(candidate)

        if not compiled.fullmatch(candidate):
            continue

        if min_len is not None and n < min_len:
            continue
        if max_len is not None and n > max_len:
            continue

        return candidate

    msg = f"Could not generate a string matching pattern {pattern!r}"
    if min_len is not None or max_len is not None:
        msg += f" with length constraints min={min_len}, max={max_len}"
    msg += " after 20 attempts."
    raise RuntimeError(msg)


def _invert_pattern_string(valid_example: str, pattern: str | None = None) -> str:
    if not valid_example:
        return "x"

    compiled = None
    if pattern:
        compiled = re.compile(pattern)

    bad_chars = [" ", "!", "@", "#", "\n", "\t", "\x00"]

    if compiled:
        for ch in bad_chars:
            candidate = valid_example + ch
            if compiled.fullmatch(candidate) is None:
                return candidate

    if compiled:
        for ch in bad_chars:
            candidate = ch + valid_example
            if compiled.fullmatch(candidate) is None:
                return candidate

    if compiled:
        for ch in bad_chars:
            candidate = ch + valid_example[1:]
            if compiled.fullmatch(candidate) is None:
                return candidate

    first = valid_example[0]
    if first.isalpha():
        invalid = "1"
    elif first.isdigit():
        invalid = "a"
    else:
        invalid = "x"
    return invalid + valid_example[1:]
