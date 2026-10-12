from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from .base import Constraint

TNum = int | float
TBound = TNum | datetime | date | time | timedelta


@dataclass(frozen=True, slots=True)
class GreaterThan(Constraint):
    value: TBound

    def __repr__(self) -> str:
        return f"GreaterThan(value={self.value})"


@dataclass(frozen=True, slots=True)
class GreaterOrEqual(Constraint):
    value: TBound

    def __repr__(self) -> str:
        return f"GreaterOrEqual(value={self.value})"


@dataclass(frozen=True, slots=True)
class LessThan(Constraint):
    value: TBound

    def __repr__(self) -> str:
        return f"LessThan(value={self.value})"


@dataclass(frozen=True, slots=True)
class LessOrEqual(Constraint):
    value: TBound

    def __repr__(self) -> str:
        return f"LessOrEqual(value={self.value})"


@dataclass(frozen=True, slots=True)
class MultipleOf(Constraint):
    value: TNum

    def __repr__(self) -> str:
        return f"MultipleOf(value={self.value})"
