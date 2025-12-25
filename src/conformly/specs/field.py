from dataclasses import dataclass, field
from typing import Any

from conformly.constraints import Constraint

_UNSET = object()

# TODO: зафиксировать уже логику обязательности


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: type
    constraints: list[Constraint] = field(default_factory=list)
    default: Any = _UNSET
    nullable: bool = False

    def has_default(self) -> bool:
        return self.default is not _UNSET

    def is_optional(self) -> bool:
        return self.nullable

    def __repr__(self) -> str:
        return (
            f"Field(name={self.name!r}, "
            f"type={self.type!r}, "
            f"constraints={[repr(c) for c in self.constraints]!r})"
        )
