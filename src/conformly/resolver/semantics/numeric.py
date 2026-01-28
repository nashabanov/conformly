from dataclasses import dataclass
from typing import Literal

from ...types import FieldKind, Range


@dataclass(frozen=True)
class NumericSemantic:
    kind: Literal[FieldKind.INTEGER, FieldKind.FLOAT]
    valid_range: Range
    invalid_ranges: tuple[Range, ...]
    has_constraints: bool
