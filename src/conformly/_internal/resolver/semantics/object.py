from dataclasses import dataclass

from .base import BaseSemantic

from conformly._internal.types import FieldKind


@dataclass(frozen=True, slots=True)
class ObjectSemantic(BaseSemantic):
    @property
    def kind(self) -> FieldKind:
        return FieldKind.OBJECT
