from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .model import ModelSpec

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
    nested_model: ModelSpec | None = None

    def has_default(self) -> bool:
        return self.default is not _UNSET

    def is_optional(self) -> bool:
        return self.nullable

    def __repr__(self) -> str:
        parts = [
            f"name={self.name!r}",
            f"type={self.type!r}",
        ]
        if self.constraints:
            parts.append(f"constraints={[repr(c) for c in self.constraints]!r}")
        if self.nested_model:
            parts.append(f"nested_model={self.nested_model!r}")

        return f"Field({', '.join(parts)})"
