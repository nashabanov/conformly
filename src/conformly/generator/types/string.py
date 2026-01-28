import random
import re
import string

import rstr

from conformly.resolver.semantics.string import StringSemantic
from conformly.types import ViolationType

DEFAULT_MIN_LENGTH = 5
DEFAULT_MAX_LENGTH = 15
DEFAULT_CHARSET = string.ascii_letters + string.digits
MAX_GENERATION_ATTEMPTS = 20
MAX_CANDIDATE_LENGTH = 1000
BAD_CHARS_FOR_INVERSION = [" ", "!", "@", "#", "\n", "\t", "\x00"]


def generate_value(semantic: StringSemantic, violation: ViolationType | None) -> str:
    return (
        _generate_valid_string(semantic)
        if not violation
        else _generate_invalid_string(semantic, violation)
    )


def _generate_valid_string(semantic: StringSemantic) -> str:
    if semantic.pattern:
        return _random_pattern_with_length(
            semantic.pattern,
            semantic.length_range.min_length,
            semantic.length_range.max_length,
        )

    return _random_string_with_length(
        semantic.length_range.min_length, semantic.length_range.max_length
    )


def _generate_invalid_string(
    semantic: StringSemantic, violation: ViolationType | None
) -> str:
    match violation:
        case ViolationType.TOO_SHORT if semantic.length_range.min_length > 0:
            return _random_string_fixed_length(semantic.length_range.min_length - 1)

        case ViolationType.TOO_LONG if semantic.length_range.max_length is not None:
            return _random_string_fixed_length(semantic.length_range.max_length + 1)

        case ViolationType.PATTERN_MISMATCH if semantic.pattern is not None:
            valid_example = rstr.xeger(semantic.pattern)
            return _invert_pattern_string(valid_example, semantic.pattern)

        case _:
            return "INVALID"


def _random_string_with_length(min_len: int, max_len: int | None) -> str:
    if max_len is None:
        length = random.randint(min_len, min_len + 50)
    else:
        length = random.randint(min_len, max_len)

    return rstr.rstr(DEFAULT_CHARSET, length)


def _random_string_fixed_length(length: int) -> str:
    if length < 0:
        raise ValueError("Length must be non-negative")
    if length == 0:
        return ""
    return rstr.rstr(DEFAULT_CHARSET + string.digits, length)


def _random_pattern_with_length(pattern: str, min_len: int, max_len: int | None) -> str:
    if max_len is not None and min_len > max_len:
        raise ValueError("min_len cannot be greater than max_len")

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
    for _ in range(MAX_GENERATION_ATTEMPTS):
        try:
            candidate = rstr.xeger(pattern)
        except Exception as e:
            raise ValueError(f"Invalid or unsupported regex pattern: {pattern}") from e

        if len(candidate) > MAX_CANDIDATE_LENGTH:
            continue
        if not compiled.fullmatch(candidate):
            continue
        if len(candidate) < min_len:
            continue
        if max_len is not None and len(candidate) > max_len:
            continue

        return candidate

    msg = f"Could not generate a string matching pattern {pattern!r}"
    if max_len is not None:
        msg += f" with length constraints min={min_len}, max={max_len}"
    msg += " after 20 attempts."
    raise RuntimeError(msg)


def _invert_pattern_string(valid_example: str, pattern: str) -> str:
    if not valid_example:
        return "x"

    compiled = re.compile(pattern)

    for ch in BAD_CHARS_FOR_INVERSION:
        candidate = valid_example + ch
        if compiled.fullmatch(candidate) is None:
            return candidate

    for ch in BAD_CHARS_FOR_INVERSION:
        candidate = ch + valid_example
        if compiled.fullmatch(candidate) is None:
            return candidate

    for ch in BAD_CHARS_FOR_INVERSION:
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
