from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..types import FieldPath
    from .model import ResolvedModel
    from .semantics import FieldSemantics


@dataclass(frozen=True)
class ResolvedField:
    name: str
    path: FieldPath
    py_type: type
    default: Any
    nullable: bool
    semantic: FieldSemantics
    nested_model: ResolvedModel | None = None
