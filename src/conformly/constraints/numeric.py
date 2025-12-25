from dataclasses import dataclass

from .base import Constraint

TNum = int | float


@dataclass(frozen=True)
class GreaterThan(Constraint):
    value: TNum

    def __repr__(self) -> str:
        return f"GreaterThan(value={self.value})"


@dataclass(frozen=True)
class GreaterOrEqual(Constraint):
    value: TNum

    def __repr__(self) -> str:
        return f"GreaterOrEqual(value={self.value})"


@dataclass(frozen=True)
class LessThan(Constraint):
    value: TNum

    def __repr__(self) -> str:
        return f"LessThan(value={self.value})"


@dataclass(frozen=True)
class LessOrEqual(Constraint):
    value: TNum

    def __repr__(self) -> str:
        return f"LessOrEqual(value={self.value})"
