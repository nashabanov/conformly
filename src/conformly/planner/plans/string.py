from dataclasses import dataclass
from enum import Enum, auto

from ...resolver.semantics.string import LengthRange


class StringViolationKind(Enum):
    TOO_LONG = auto()
    TOO_SHORT = auto()
    PATTERN_MISMATCH = auto()


@dataclass(frozen=True)
class StringGeneration:
    valid_length_range: LengthRange
    pattern: str | None


@dataclass(frozen=True)
class StringViolation:
    kind: StringViolationKind
    invalid_length_range: LengthRange
    pattern: str | None
