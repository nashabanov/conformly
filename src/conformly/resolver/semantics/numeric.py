from dataclasses import dataclass
from typing import Literal

from ...types import FieldKind


@dataclass(frozen=True)
class Range:
    min_value: int | float
    max_value: int | float
    has_min: bool
    has_max: bool


@dataclass(frozen=True)
class NumericSemantic:
    kind: Literal[FieldKind.INTEGER, FieldKind.FLOAT]
    valid_range: Range
    invalid_ranges: tuple[Range, ...]
