from dataclasses import dataclass
from enum import Enum, auto


class ObjectViolationKind(Enum):
    NOT_OBJECT = auto()
    MISSING_FIELD = auto()
    EXTRA_FIELD = auto()


@dataclass(frozen=True)
class ObjectGeneration:
    pass


@dataclass(frozen=True)
class ObjectViolation:
    kind: ObjectViolationKind
