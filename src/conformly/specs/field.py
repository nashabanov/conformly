from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..types import _UNSET

if TYPE_CHECKING:
    from ..constraints import Constraint
    from .model import ModelSpec


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: type
    constraints: tuple[Constraint, ...] = ()
    default: Any = _UNSET
    nullable: bool = False
    nested_model: ModelSpec | None = None

    def has_default(self) -> bool:
        return self.default is not _UNSET

    def is_optional(self) -> bool:
        return self.nullable

    def has_constraints(self) -> bool:
        return len(self.constraints) > 0

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
