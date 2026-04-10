from dataclasses import dataclass

from conformly._internal.types import FieldPath, ViolationType


@dataclass(frozen=True)
class PlannedTask:
    path: FieldPath
    allowed_violations: tuple[ViolationType, ...]
