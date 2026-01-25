from dataclasses import dataclass
from enum import Enum, auto

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


@dataclass(frozen=True)
class Range:
    min_value: int | float
    max_value: int | float
    has_min: bool
    has_max: bool


@dataclass(frozen=True)
class LengthRange:
    min_length: int
    max_length: int | None
    has_min: bool
    has_max: bool
