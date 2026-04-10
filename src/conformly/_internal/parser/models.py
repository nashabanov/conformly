from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from ..types import UNSET

if TYPE_CHECKING:
    from ..constraints import Constraint


@dataclass(frozen=True)
class FieldSpec:
    name: str
    field_type: type
    constraints: tuple[Constraint, ...] = ()
    default: Any = UNSET
    nullable: bool = False
    nested_model: ModelSpec | None = None
    collection_type: type | None = None

    def has_default(self) -> bool:
        return self.default is not UNSET

    def is_optional(self) -> bool:
        return self.nullable

    def has_constraints(self) -> bool:
        return len(self.constraints) > 0

    def __repr__(self) -> str:
        parts = [
            f"name={self.name!r}",
            f"type={self.field_type!r}",
        ]
        if self.constraints:
            parts.append(f"constraints={[repr(c) for c in self.constraints]!r}")
        if self.nested_model:
            parts.append(f"nested_model={self.nested_model!r}")

        return f"Field({', '.join(parts)})"


ModelType = Literal["dataclass", "pydantic"]


@dataclass(frozen=True)
class ModelSpec:
    name: str
    type: ModelType
    fields: tuple[FieldSpec, ...]

    def get_field(self, field_name: str) -> FieldSpec:
        for field in self.fields:
            if field.name == field_name:
                return field
        raise KeyError(f"Field '{field_name}' is not defined in model: '{self.name}'")

    def get_requiered_fields(self) -> list[FieldSpec]:
        return [field for field in self.fields if not field.has_default()]

    def get_optional_fields(self) -> list[FieldSpec]:
        return [field for field in self.fields if field.is_optional()]

    def __repr__(self) -> str:
        return (
            f"Model(name={self.name!r}, "
            f"type={self.type!r}, "
            f"fields={[repr(f) for f in self.fields]!r})"
        )
