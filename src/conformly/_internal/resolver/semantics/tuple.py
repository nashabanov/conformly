from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import BaseSemantic

from conformly._internal.types import FieldKind, LengthRange

if TYPE_CHECKING:
    from ..models import ResolvedModel
    from . import FieldSemantics


@dataclass(frozen=True, slots=True)
class TupleSemantic(BaseSemantic):
    elements_semantics: dict["FieldSemantics", "ResolvedModel | None"]
    length_range: LengthRange | None = None
    is_unique_items: bool = False

    @property
    def kind(self) -> FieldKind:
        return FieldKind.TUPLE
