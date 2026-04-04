from dataclasses import dataclass
from typing import Any

from ...types import FieldKind


@dataclass(frozen=True)
class EnumSemantic:
    values: tuple[Any, ...]
    has_constraints: bool

    @property
    def kind(self) -> FieldKind:
        return FieldKind.ENUM
