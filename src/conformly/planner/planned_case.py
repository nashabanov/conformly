from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..types import FieldKind, FieldPath
    from .plans import GenerationPlan, ViolationPlan


@dataclass(frozen=True)
class PlannedField:
    name: str
    path: FieldPath
    kind: FieldKind
    nullable: bool
    default: Any
    generation_plan: GenerationPlan | None
    violation_spec: ViolationPlan | None
    nested: PlannedObject | None


@dataclass(frozen=True)
class PlannedObject:
    name: str
    fields: tuple[PlannedField, ...]


@dataclass(frozen=True)
class PlannedCase:
    root: PlannedObject
    violated_path: FieldPath | None
