from collections.abc import Sequence
from typing import Any, Protocol

from conformly.constraints import Constraint
from conformly.specs.field import FieldSpec


class TypeGeneratorProtocol(Protocol):
    """Interface that all generators must implement"""

    def supports(self, field: FieldSpec) -> bool:
        """Return True if generator returns with type"""
        ...

    def generate_value(self, constraints: Sequence[Constraint], valid: bool) -> Any:
        """Return valid or invalid value of supported type based on constraints"""
        ...
