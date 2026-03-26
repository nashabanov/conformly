from dataclasses import dataclass
from enum import Enum
import math
from typing import Literal

FieldPath = tuple[int, ...]


CaseStrategy = Literal["first", "random"] | str
CasesStrategy = Literal["first", "random", "all", "all_violations"] | str


class FieldKind(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ENUM = "enum"
    EMAIL = "email"


class ViolationType(Enum):
    # numeric
    BELOW_MIN = "below_min"
    ABOVE_MAX = "above_max"
    NOT_MULTIPLE = "not_multiple"

    # string
    TOO_LONG = "too_long"
    TOO_SHORT = "too_short"
    PATTERN_MISMATCH = "pattern_mismatch"

    # typing
    TYPE_MISMATCH = "type_mismatch"
    NONE_FOR_NOT_OPTIONAL = "none_for_not_optional"

    # Enum
    NOT_ALLOWED_VALUE = "not_allowed_value"

    # structural
    MISSING_FIELD = "missing_field"
    EXTRA_FIELD = "extra_field"


INT_MIN = -(2**63)
INT_MAX = 2**63 - 1
FLOAT_MIN = -math.inf
FLOAT_MAX = math.inf


@dataclass(frozen=True)
class Range:
    min_value: int | float
    max_value: int | float


@dataclass(frozen=True)
class LengthRange:
    min_length: int
    max_length: int | None


ENUMERATED_TYPE = type("EnummeratedType", (), {})


_UNSET = object()
