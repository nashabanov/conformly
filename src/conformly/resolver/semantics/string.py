from dataclasses import dataclass
from re import Pattern
from typing import Literal

from ...types import FieldKind


@dataclass(frozen=True)
class StringSemantic:
    kind: Literal[FieldKind.STRING]
    min_length: int
    max_length: int
    pattern: Pattern
