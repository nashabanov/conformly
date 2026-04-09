from dataclasses import dataclass


@dataclass(frozen=True)
class Range:
    min_value: int | float
    max_value: int | float


@dataclass(frozen=True)
class LengthRange:
    min_length: int
    max_length: int | None
