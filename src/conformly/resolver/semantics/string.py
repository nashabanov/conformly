from dataclasses import dataclass
from typing import Literal

from ...types import FieldKind


@dataclass(frozen=True)
class LengthRange:
    min_length: int
    max_length: int | None
    has_min: bool
    has_max: bool


@dataclass(frozen=True)
class StringSemantic:
    kind: Literal[FieldKind.STRING]
    length_range: LengthRange
    pattern: str | None
