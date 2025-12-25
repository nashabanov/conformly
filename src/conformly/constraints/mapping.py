from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .numeric import GreaterOrEqual, GreaterThan, LessOrEqual, LessThan
from .string import MaxLength, MinLength, Pattern

if TYPE_CHECKING:
    from collections.abc import Callable

    from .base import Constraint
    from .types import ConstraintType

CONSTRAINT_MAPPING: dict[ConstraintType, Callable[[Any], Constraint]] = {
    "gt": GreaterThan,
    "ge": GreaterOrEqual,
    "lt": LessThan,
    "le": LessOrEqual,
    "max_length": MaxLength,
    "min_length": MinLength,
    "pattern": Pattern,
}


def create_constraint(constraint_type: ConstraintType, value: Any) -> Constraint:
    try:
        cls = CONSTRAINT_MAPPING[constraint_type]
    except KeyError:
        raise ValueError(f"Unsupported constraint type: {constraint_type}")

    try:
        return cls(value)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Invalid value {value!r} for constraint {constraint_type}: {e!s}"
        ) from e
