from dataclasses import dataclass

from ..._internal.types import FieldKind


@dataclass(frozen=True)
class ObjectSemantic:
    has_constraints: bool = False

    @property
    def kind(self) -> FieldKind:
        return FieldKind.OBJECT
