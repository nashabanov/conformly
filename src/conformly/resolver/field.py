from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .._internal.parser import FieldSpec
    from .._internal.types import FieldPath
    from .model import ResolvedModel
    from .semantics import FieldSemantics


@dataclass(frozen=True)
class ResolvedField:
    field_spec: FieldSpec
    path: FieldPath
    semantic: FieldSemantics
    nested_model: ResolvedModel | None = None

    @property
    def name(self) -> str:
        return self.field_spec.name

    @property
    def py_type(self) -> type:
        return self.field_spec.field_type

    @property
    def default(self) -> Any:
        return self.field_spec.default

    @property
    def nullable(self) -> bool:
        return self.field_spec.nullable
