from dataclasses import dataclass
from typing import Any

from .base import BaseSemantic

from conformly._internal.types import FieldKind


@dataclass(frozen=True, slots=True)
class EnumSemantic(BaseSemantic):
    values: tuple[Any, ...] = ()

    @property
    def kind(self) -> FieldKind:
        return FieldKind.ENUM
