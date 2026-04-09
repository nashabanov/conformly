from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..._internal.types import FieldKind

if TYPE_CHECKING:
    from ..model import ResolvedModel
    from . import FieldSemantics


@dataclass(frozen=True)
class ListSemantic:
    element_semantic: "FieldSemantics"
    element_nested_model: "ResolvedModel | None" = None
    has_constraints: bool = False

    @property
    def kind(self) -> FieldKind:
        return FieldKind.LIST
