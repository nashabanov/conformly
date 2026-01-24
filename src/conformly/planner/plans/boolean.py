from dataclasses import dataclass
from enum import Enum, auto


class BooleanViolationKind(Enum):
    NOT_BOOLEAN = auto()


@dataclass(frozen=True)
class BooleanGeneration:
    pass


@dataclass(frozen=True)
class BooleanViolation:
    kind: BooleanViolationKind
