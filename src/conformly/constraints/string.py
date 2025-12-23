from dataclasses import dataclass

from .base import Constraint


@dataclass(frozen=True)
class MinLength(Constraint):
    value: int


@dataclass(frozen=True)
class MaxLength(Constraint):
    value: int


@dataclass(frozen=True)
class Pattern(Constraint):
    regex: str
