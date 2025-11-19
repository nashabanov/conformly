from typing import Any, Protocol

from conformly.specs.field import ConstraintSpec, FieldSpec


class TypeGeneratorProtocol(Protocol):
    """Interface that all generators must implement"""

    def supports(self, field: FieldSpec) -> bool:
        """Return True if generator returns with type"""
        ...

    def generate_value(self, constraints: list[ConstraintSpec], valid: bool) -> Any:
        """Return valid or invalid value of supported type based on constraints"""
        ...
