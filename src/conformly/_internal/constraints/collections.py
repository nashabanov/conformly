from dataclasses import dataclass

from .base import Constraint


@dataclass(frozen=True)
class MinItems(Constraint):
    value: int

    def __repr__(self) -> str:
        return f"MinItems(value={self.value})"


@dataclass(frozen=True)
class MaxItems(Constraint):
    value: int

    def __repr__(self) -> str:
        return f"MaxItems(value={self.value})"


@dataclass(frozen=True)
class UniqueItems(Constraint):
    is_unique: bool

    def __repr__(self) -> str:
        return f"UniqueItems(is_unique={self.is_unique})"
