from dataclasses import dataclass
from typing import Literal

from .base import BaseSemantic

from conformly._internal.types import FieldKind, Range


@dataclass(frozen=True, slots=True, kw_only=True)
class NumericSemantic(BaseSemantic):
    kind: Literal[FieldKind.INTEGER, FieldKind.FLOAT]
    valid_range: Range
    invalid_ranges: tuple[Range, ...]
    multiple_of: int | float | None = None
