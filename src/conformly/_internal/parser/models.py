from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from ..types import UNSET

if TYPE_CHECKING:
    from ..constraints import Constraint


@dataclass(frozen=True, slots=True)
class ElementSpec:
    field_type: type
    constraints: tuple[Constraint, ...] = ()
    nested_model: ModelSpec | None = None


@dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    element: ElementSpec | None = None
    collection_type: type | None = None
    collection_constraints: tuple[Constraint, ...] = ()
    item: ElementSpec | None = None
    items: tuple[ElementSpec, ...] | None = None
    key: ElementSpec | None = None
    value: ElementSpec | None = None
    nullable: bool = False
    default: Any = UNSET

    def has_default(self) -> bool:
        return self.default is not UNSET

    def is_optional(self) -> bool:
        return self.nullable

    def has_constraints(self) -> bool:
        return (
            (self.element is not None and len(self.element.constraints) != 0)
            or (self.item is not None and len(self.item.constraints) != 0)
            or (self.key is not None and len(self.key.constraints) != 0)
            or (self.value is not None and len(self.value.constraints) != 0)
            or len(self.collection_constraints) != 0
        )

    def has_nested_model(self) -> bool:
        return (
            (self.element is not None and self.element.nested_model is not None)
            or (self.item is not None and self.item.nested_model is not None)
            or (self.key is not None and self.key.nested_model is not None)
            or (self.value is not None and self.value.nested_model is not None)
        )


ModelType = Literal["dataclass", "pydantic", "typeddict", "attrs"]


@dataclass(frozen=True, slots=True)
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
