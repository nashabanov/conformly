from dataclasses import dataclass
from typing import Literal

from .field import FieldSpec

ModelType = Literal["dataclass", "pydantic"]


@dataclass(frozen=True)
class ModelSpec:
    name: str
    type: ModelType
    fields: list[FieldSpec]

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
