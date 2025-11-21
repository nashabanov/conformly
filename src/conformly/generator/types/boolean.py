from random import choice
from typing import no_type_check

from conformly.specs import ConstraintSpec, FieldSpec


def supports(field: FieldSpec) -> bool:
    return field.type is bool


@no_type_check
def generate_value(
    constraints: list[ConstraintSpec] | None = None, valid: bool | None = None
) -> bool:
    return choice([True, False])
