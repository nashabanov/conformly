from dataclasses import dataclass

from .base import Constraint

TNum = int | float


@dataclass(frozen=True)
class GreaterThan(Constraint):
    value: TNum


@dataclass(frozen=True)
class GreaterOrEqual(Constraint):
    value: TNum


@dataclass(frozen=True)
class LessThan(Constraint):
    value: TNum


@dataclass(frozen=True)
class LessOrEqual(Constraint):
    value: TNum
