from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import FieldPath
    from .field import ResolvedField


@dataclass(frozen=True)
class ResolvedModel:
    name: str
    fields: tuple[ResolvedField, ...]

    def get_field(self, path: FieldPath) -> ResolvedField:
        return _get_field(self, path)


def _get_field(model: ResolvedModel, path: FieldPath) -> ResolvedField:
    head = path[0]
    tail = path[1:]

    if not (0 <= head < len(model.fields)):
        raise IndexError(
            f"Index {head} out of range for model '{model.name}' "
            f"with {len(model.fields)} fields"
        )

    field = model.fields[head]

    if not tail:
        return field

    if field.nested_model is None:
        raise ValueError(f"Cannot traverse into non-nested field '{field.name}'")

    return _get_field(field.nested_model, tail)
