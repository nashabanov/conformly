from dataclasses import dataclass

from .base import Constraint


@dataclass(frozen=True, slots=True)
class MinLength(Constraint):
    value: int

    def __repr__(self) -> str:
        return f"MinLength(value={self.value})"


@dataclass(frozen=True, slots=True)
class MaxLength(Constraint):
    value: int

    def __repr__(self) -> str:
        return f"MaxLength(value={self.value})"


@dataclass(frozen=True, slots=True)
class Pattern(Constraint):
    regex: str

    def __repr__(self) -> str:
        return f"Pattern(regex={self.regex})"
