from collections.abc import Sequence
from random import choice
from typing import no_type_check

from conformly.constraints import Constraint
from conformly.specs import FieldSpec


def supports(field: FieldSpec) -> bool:
    return field.type is bool


@no_type_check
def generate_value(
    constraints: Sequence[Constraint] | None = None, valid: bool | None = None
) -> bool:
    return choice([True, False])
