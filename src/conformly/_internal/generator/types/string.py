import re
import string

from .._errors import generation_error
from ..context import GenerationContext

from conformly._internal.resolver.semantics._regex import is_universal_pattern
from conformly._internal.resolver.semantics.string import StringSemantic
from conformly._internal.types import MAX_GENERATION_ATTEMPTS, ViolationType

DEFAULT_MIN_LENGTH = 5
DEFAULT_MAX_LENGTH = 15
DEFAULT_CHARSET = string.ascii_letters + string.digits
MAX_CANDIDATE_LENGTH = 1000
BAD_CHARS_FOR_INVERSION = [" ", "!", "@", "#", "\n", "\t", "\x00"]


def generate_value(
    ctx: GenerationContext, semantic: StringSemantic, violation: ViolationType | None
) -> str:
    return (
        _generate_valid_string(ctx, semantic)
        if not violation
        else _generate_invalid_string(ctx, semantic, violation)
    )


def _generate_valid_string(ctx: GenerationContext, semantic: StringSemantic) -> str:
    if semantic.pattern is not None:
        return _random_pattern_with_length(
            ctx,
            semantic.pattern,
            semantic.length_range.min_length,
            semantic.length_range.max_length,
        )

    return _random_string_with_length(
        ctx, semantic.length_range.min_length, semantic.length_range.max_length
    )


def _generate_invalid_string(
    ctx: GenerationContext, semantic: StringSemantic, violation: ViolationType | None
) -> str:
    match violation:
        case ViolationType.TOO_SHORT if semantic.length_range.min_length > 0:
            return _random_string_fixed_length(
                ctx, semantic.length_range.min_length - 1
            )

        case ViolationType.TOO_LONG if semantic.length_range.max_length is not None:
            return _random_string_fixed_length(
                ctx, semantic.length_range.max_length + 1
            )

        case ViolationType.PATTERN_MISMATCH if semantic.pattern is not None:
            # Inversion must also work when xeger cannot synthesize the pattern.
            return _invert_pattern_string("", semantic.pattern)

        case _:
            raise generation_error(
                "Unsupported string violation",
                code="unsupported_violation",
                violation=violation.value if violation else None,
            )


def _random_string_with_length(
    ctx: GenerationContext, min_len: int, max_len: int | None
) -> str:
    if max_len is None:
        length = ctx.rng.randint(min_len, min_len + 50)
    else:
        length = ctx.rng.randint(min_len, max_len)

    return ctx.rstr.rstr(DEFAULT_CHARSET, length)


def _random_string_fixed_length(ctx: GenerationContext, length: int) -> str:
    if length < 0:
        raise generation_error(
            "String length must be non-negative",
            code="invalid_string_length",
            length=length,
        )
    if length == 0:
        return ""
    return ctx.rstr.rstr(DEFAULT_CHARSET + string.digits, length)


def _random_pattern_with_length(
    ctx: GenerationContext, pattern: str, min_len: int, max_len: int | None
) -> str:
    if max_len is not None and min_len > max_len:
        raise generation_error(
            "min_len cannot be greater than max_len",
            code="invalid_length_constraints",
            min_len=min_len,
            max_len=max_len,
        )

    compiled = None
    try:
        compiled = re.compile(pattern)
    except re.error as e:
        raise generation_error(
            "Invalid or unsupported regex pattern",
            code="invalid_regex_pattern",
            pattern=pattern,
        ) from e

    if min_len == 0 and compiled.search(""):
        return ""

    if min_len == 0 and max_len == 0:
        empty_ok = compiled.search("")
        if empty_ok:
            return ""
        else:
            raise generation_error(
                "Pattern doesn`t allow empty string, but length constraints require it",
                code="pattern_empty_string_conflict",
                pattern=pattern,
            )
    for _ in range(MAX_GENERATION_ATTEMPTS):
        try:
            candidate = ctx.rstr.xeger(pattern)
        except Exception as e:
            raise generation_error(
                "Failed to generate string from regex pattern",
                code="regex_generation_failed",
                pattern=pattern,
            ) from e

        if len(candidate) > MAX_CANDIDATE_LENGTH:
            continue
        if not compiled.search(candidate):
            continue
        if len(candidate) < min_len:
            continue
        if max_len is not None and len(candidate) > max_len:
            continue

        return candidate

    raise generation_error(
        "Could not generate a string matching pattern within length constraints",
        code="pattern_generation_timeout",
        pattern=pattern,
        min_len=min_len,
        max_len=max_len,
        attempts=MAX_GENERATION_ATTEMPTS,
    )


def _invert_pattern_string(valid_example: str, pattern: str) -> str:
    try:
        compiled = re.compile(pattern)
    except re.error as e:
        raise generation_error(
            "Invalid or unsupported regex pattern",
            code="invalid_regex_pattern",
            pattern=pattern,
        ) from e

    if is_universal_pattern(pattern):
        raise generation_error(
            "Pattern matches every string under search semantics",
            code="impossible_violation",
            violation=ViolationType.PATTERN_MISMATCH.value,
            pattern=pattern,
        )

    candidates = ["x", "", "a", "1", *BAD_CHARS_FOR_INVERSION]
    for ch in BAD_CHARS_FOR_INVERSION:
        candidates.extend(
            (valid_example + ch, ch + valid_example, ch + valid_example[1:])
        )
    candidates.extend(
        ch * length for length in (2, 8, 32) for ch in DEFAULT_CHARSET + "\n\x00"
    )
    for candidate in candidates:
        if compiled.search(candidate) is None:
            return candidate

    raise generation_error(
        "Could not find a string that does not match the pattern",
        code="pattern_inversion_exhausted",
        pattern=pattern,
        attempts=len(candidates),
    )
