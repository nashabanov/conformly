from dataclasses import dataclass

from conformly._internal.types import FieldKind


@dataclass(frozen=True, slots=True, kw_only=True)
class BaseSemantic:
    has_constraints: bool = False

    @property
    def kind(self) -> FieldKind:
        raise NotImplementedError()
