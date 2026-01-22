from dataclasses import dataclass
from typing import Any

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
    semantics: list[FieldSemantics]
    nested_model: ResolvedModel | None = None
