from dataclasses import dataclass
from typing import Literal

from ...types import FieldKind


@dataclass(frozen=True)
class ObjectSemantic:
    kind: Literal[FieldKind.OBJECT]
    has_constraints: bool = False
