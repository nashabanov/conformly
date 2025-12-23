from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .numeric import GreaterOrEqual, GreaterThan, LessOrEqual, LessThan
from .string import MaxLength, MinLength, Pattern

if TYPE_CHECKING:
    from collections.abc import Callable

    from .base import Constraint

    from conformly.specs import ConstraintSpec, ConstraintType

CONSTRAINT_MAPPING: dict[ConstraintType, Callable[[Any], Constraint]] = {
    "gt": GreaterThan,
    "ge": GreaterOrEqual,
    "lt": LessThan,
    "le": LessOrEqual,
    "max_length": MaxLength,
    "min_length": MinLength,
    "pattern": Pattern,
}


def constraint_from_spec(spec: ConstraintSpec) -> Constraint:
    cls = CONSTRAINT_MAPPING[spec.constraint_type]
    return cls(spec.value)
