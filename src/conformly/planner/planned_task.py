from dataclasses import dataclass

from ..types import FieldPath, ViolationType


@dataclass(frozen=True)
class PlannedTask:
    path: FieldPath
    allowed_violations: tuple[ViolationType, ...]
