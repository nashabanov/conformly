from dataclasses import dataclass
from enum import Enum, auto

from ...resolver.semantics.numeric import Range


class NumericViolationKind(Enum):
    BELLOW_MIN = auto()
    ABOVE_MAX = auto()


@dataclass(frozen=True)
class NumericGeneration:
    valid_range: Range


@dataclass(frozen=True)
class NumericViolation:
    kind: NumericViolationKind
    invalid_range: Range
