from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...types import FieldKind

if TYPE_CHECKING:
    from . import FieldSemantics


@dataclass(frozen=True)
class ListSemantic:
    element_semantic: "FieldSemantics"
    has_constraints: bool = False

    @property
    def kind(self) -> FieldKind:
        return FieldKind.LIST
