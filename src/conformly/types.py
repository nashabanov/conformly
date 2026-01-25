from dataclasses import dataclass
from enum import Enum, auto
import math

FieldPath = tuple[int, ...]


class FieldKind(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    OBJECT = "object"


class ViolationType(Enum):
    # numeric
    BELOW_MIN = auto()
    ABOVE_MAX = auto()

    # string
    TOO_LONG = auto()
    TOO_SHORT = auto()
    PATTERN_MISMATCH = auto()

    # typing
    TYPE_MISMATCH = auto()
    NONE_FOR_NOT_OPTIONAL = auto()

    # structural
    MISSING_FIELD = auto()
    EXTRA_FIELD = auto()


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
