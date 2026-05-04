from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from conformly.exceptions import ResolutionError

if TYPE_CHECKING:
    from .semantics import FieldSemantics

    from conformly._internal.parser import FieldSpec
    from conformly._internal.types import FieldPath


@dataclass(frozen=True, slots=True)
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
        if self.field_spec.element is not None:
            return self.field_spec.element.field_type
        if self.field_spec.item is not None:
            return self.field_spec.item.field_type
        if self.field_spec.key is not None:
            return self.field_spec.key.field_type
        if self.field_spec.value is not None:
            return self.field_spec.value.field_type
        return object

    @property
    def default(self) -> Any:
        return self.field_spec.default

    @property
    def nullable(self) -> bool:
        return self.field_spec.is_optional()


@dataclass(frozen=True, slots=True)
class ResolvedModel:
    name: str
    fields: tuple[ResolvedField, ...]
    field_map: dict[FieldPath, ResolvedField] = field(default_factory=dict, repr=False)
    constrained_paths: tuple[FieldPath, ...] = field(default_factory=tuple, repr=False)
    all_paths: tuple[FieldPath, ...] = field(default_factory=tuple, repr=False)
    extra_paths: tuple[FieldPath, ...] = field(default_factory=tuple, repr=False)
    name_to_path: dict[str, FieldPath] = field(default_factory=dict, repr=False)

    def get_field(self, path: FieldPath) -> ResolvedField:
        if path not in self.field_map:
            if not path:
                raise ValueError("Empty path")

            parent_path = path[:-1]
            if parent_path and parent_path not in self.field_map:
                raise IndexError(f"Parent path {parent_path} not found")

            raise ResolutionError(
                f"Path {path} refers to an extra field",
                context={
                    "code": "extra_field_path",
                    "path": path,
                    "model": self.name,
                    "field_count": len(self.fields),
                },
            )

        return self.field_map[path]
