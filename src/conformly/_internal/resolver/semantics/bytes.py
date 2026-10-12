from dataclasses import dataclass

from .base import BaseSemantic

from conformly._internal.constraints import Constraint, MaxLength, MinLength
from conformly._internal.types import FieldKind, LengthRange
from conformly.exceptions import SchemaError


@dataclass(frozen=True, slots=True, kw_only=True)
class BytesSemantic(BaseSemantic):
    length_range: LengthRange

    @property
    def kind(self) -> FieldKind:
        return FieldKind.BYTES


def create_bytes_semantic(constraints: tuple[Constraint, ...]) -> BytesSemantic:
    lower = 0
    upper: int | None = None
    for constraint in constraints:
        if not isinstance(constraint, (MinLength, MaxLength)):
            raise SchemaError(
                "Bytes fields only support MinLength and MaxLength",
                context={
                    "code": "unsupported_bytes_constraint",
                    "constraint": type(constraint).__name__,
                },
            )
        value = constraint.value
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise SchemaError(
                "Bytes length must be a non-negative integer",
                context={"code": "invalid_bytes_length", "value": value},
            )
        if isinstance(constraint, MinLength):
            lower = max(lower, value)
        else:
            upper = value if upper is None else min(upper, value)
    if upper is not None and lower > upper:
        raise SchemaError(
            "Invalid bytes length range",
            context={"code": "invalid_length_range", "min": lower, "max": upper},
        )
    return BytesSemantic(
        length_range=LengthRange(lower, upper), has_constraints=bool(constraints)
    )
