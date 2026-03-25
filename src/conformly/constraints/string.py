from dataclasses import dataclass

from .base import Constraint


@dataclass(frozen=True)
class MinLength(Constraint):
    value: int

    def __repr__(self) -> str:
        return f"MinLength(value={self.value})"


@dataclass(frozen=True)
class MaxLength(Constraint):
    value: int

    def __repr__(self) -> str:
        return f"MaxLength(value={self.value})"


@dataclass(frozen=True)
class Pattern(Constraint):
    regex: str

    def __repr__(self) -> str:
        return f"Pattern(regex={self.regex})"


@dataclass(frozen=True)
class Email(Pattern):
    REGEX = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

    def __init__(self) -> None:
        super().__init__(regex=self.REGEX)

    def __repr__(self) -> str:
        return "Email()"
