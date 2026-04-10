from dataclasses import dataclass

from .base import BaseSemantic

from conformly._internal.types import FieldKind


@dataclass(frozen=True, slots=True)
class BooleanSemantic(BaseSemantic):
    @property
    def kind(self) -> FieldKind:
        return FieldKind.BOOLEAN
