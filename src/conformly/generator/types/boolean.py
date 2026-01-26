from random import choice
from typing import no_type_check

from ...resolver.semantics import FieldSemantics
from ...types import ViolationType


@no_type_check
def generate_value(
    semantic: FieldSemantics, violation: ViolationType | None = None
) -> bool:
    return choice([True, False])
