from dataclasses import dataclass

from ._validators import validate_string_kind
from .base import BaseSemantic

from conformly._internal.types import FieldKind, LengthRange


@dataclass(frozen=True, slots=True, kw_only=True)
class StringSemantic(BaseSemantic):
    kind: FieldKind
    length_range: LengthRange
    pattern: str | None

    def __post_init__(self) -> None:
        validate_string_kind(self.kind)
