from dataclasses import dataclass
from typing import Literal

from ...types import FieldKind, LengthRange


@dataclass(frozen=True)
class StringSemantic:
    kind: Literal[FieldKind.STRING]
    length_range: LengthRange
    pattern: str | None
    has_constraints: bool
