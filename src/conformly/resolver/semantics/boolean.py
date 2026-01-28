from dataclasses import dataclass
from typing import Literal

from ...types import FieldKind


@dataclass(frozen=True)
class BooleanSemantic:
    kind: Literal[FieldKind.BOOLEAN]
    has_constraints: bool = False
