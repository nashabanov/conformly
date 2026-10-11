from dataclasses import dataclass
from typing import Literal

from conformly._internal.types import FieldPath, ViolationType


@dataclass(frozen=True, slots=True)
class CollectionTarget:
    side: Literal["element", "key", "value"]
    index: int = 0


@dataclass(frozen=True, slots=True)
class PlannedTask:
    path: FieldPath
    allowed_violations: tuple[ViolationType, ...]
    collection_target: CollectionTarget | None = None
    collection_steps: tuple[tuple[FieldPath, CollectionTarget], ...] = ()
