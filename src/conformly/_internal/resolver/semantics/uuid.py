from dataclasses import dataclass

from .base import BaseSemantic

from conformly._internal.types import FieldKind


@dataclass(frozen=True, slots=True)
class UUIDSemantic(BaseSemantic):
    version: int = 0

    @property
    def kind(self) -> FieldKind:
        return FieldKind.UUID
