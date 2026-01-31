from dataclasses import dataclass
from typing import Any, Literal

from ...types import FieldKind


@dataclass(frozen=True)
class EnumSemantic:
    kind: Literal[FieldKind.ENUM]
    values: tuple[Any, ...]
    has_constraints: bool
