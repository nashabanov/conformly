from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import FieldPath
    from .field import ResolvedField


@dataclass(frozen=True)
class ResolvedModel:
    name: str
    fields: tuple[ResolvedField, ...]
    field_map: dict[FieldPath, ResolvedField] = field(default_factory=dict, repr=False)
    constrained_paths: tuple[FieldPath, ...] = field(default_factory=tuple, repr=False)
    all_paths: tuple[FieldPath, ...] = field(default_factory=tuple, repr=False)

    def get_field(self, path: FieldPath) -> ResolvedField:
        if path not in self.field_map:
            if not path:
                raise IndexError("Empty path")

            parent_path = path[:-1]
            if parent_path and parent_path not in self.field_map:
                raise IndexError(f"Parent path {parent_path} not found")

            raise IndexError(
                f"Path {path} is an extra field (not in field_map). "
                f"Model '{self.name}' has {len(self.fields)} fields."
            )

        return self.field_map[path]
