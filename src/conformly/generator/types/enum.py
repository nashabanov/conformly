from random import choice, randint
from typing import Any

from ...resolver.semantics import EnumSemantic
from ...types import ViolationType

_INVALID_ENUM_PREFIX = "__INVALID_ENUM_"


def generate_value(semantic: EnumSemantic, violation: ViolationType | None) -> Any:
    if violation is None:
        return choice(semantic.values)

    if violation is ViolationType.NOT_ALLOWED_VALUE:
        return _generate_not_allowed_value(semantic)

    raise ValueError(
        f"For enum semantic allowed only NONE_FOR_NOT_OPTIONAL violation, "
        f"but got {violation}"
    )


def _generate_not_allowed_value(semantic: EnumSemantic) -> Any:
    values = semantic.values
    first_type = type(values[0])
    is_homogeneous = all(type(v) is first_type for v in values)

    if is_homogeneous:
        base = choice(values)

        if first_type is str:
            suffix = f"{_INVALID_ENUM_PREFIX}{randint(10, 1000)}"
            return base + suffix

        elif first_type is int:
            for candidate in (base + 1, base - 1, base * 2 + 1, base * 2 - 1):
                if candidate not in values:
                    return candidate
            return 9_999_999

        elif first_type is float:
            for candidate in (base + 0.12, base - 0.65, base * 2.1 + 1.0):
                if candidate not in values:
                    return candidate
            return 9_999_999.999

        elif first_type is bool:
            if len(values) == 1:
                return not base

    return f"{_INVALID_ENUM_PREFIX}{randint(1_000_000, 9_999_999)}__"
