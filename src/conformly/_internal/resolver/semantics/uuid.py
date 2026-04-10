from dataclasses import dataclass

from conformly._internal.types import FieldKind


@dataclass(frozen=True)
class UUIDSemantic:
    vesrion: int = 0
    has_constraints: bool = False

    @property
    def kind(self) -> FieldKind:
        return FieldKind.UUID
