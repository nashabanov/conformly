from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import BaseSemantic

from conformly._internal.types import FieldKind, LengthRange

if TYPE_CHECKING:
    from ..models import ResolvedModel
    from . import FieldSemantics


@dataclass(frozen=True, slots=True)
class TupleSemantic(BaseSemantic):
    elements_semantics: tuple[tuple["FieldSemantics", "ResolvedModel | None"], ...]
    length_range: LengthRange | None = None
    is_variadic: bool = False

    @property
    def kind(self) -> FieldKind:
        return FieldKind.TUPLE
