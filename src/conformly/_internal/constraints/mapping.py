from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .numeric import GreaterOrEqual, GreaterThan, LessOrEqual, LessThan, MultipleOf
from .string import MaxLength, MinLength, Pattern

from conformly.exceptions import SchemaError

if TYPE_CHECKING:
    from collections.abc import Callable

    from .base import Constraint
    from .keys import ConstraintType

CONSTRAINT_MAPPING: dict[ConstraintType, Callable[[Any], Constraint]] = {
    "gt": GreaterThan,
    "ge": GreaterOrEqual,
    "lt": LessThan,
    "le": LessOrEqual,
    "max_length": MaxLength,
    "min_length": MinLength,
    "pattern": Pattern,
    "multiple_of": MultipleOf,
}


def create_constraint(constraint_type: ConstraintType, value: Any) -> Constraint:
    try:
        cls = CONSTRAINT_MAPPING[constraint_type]
    except KeyError as e:
        raise SchemaError(
            f"Unsupported constraint type: {constraint_type}",
            context={
                "code": "unsupported_constraint_type",
                "constraint_type": {constraint_type},
            },
        ) from e

    try:
        return cls(value)
    except (TypeError, ValueError) as e:
        raise SchemaError(
            f"Invalid value {value!r} for constraint {constraint_type}: {e!s}",
            context={
                "code": "invalid_constraint_value",
                "constraint_type": constraint_type,
                "value": value,
                "error": e,
            },
        ) from e
