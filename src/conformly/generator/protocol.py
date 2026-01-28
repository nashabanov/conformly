from typing import Any, Protocol

from ..types import ViolationType


class TypeGeneratorProtocol(Protocol):
    """Interface for all type-specific generators"""

    def generate_value(self, semantic: Any, violation: ViolationType | None) -> Any:
        """
        Generate a value from field semantic

        Args:
            semantic: pre-resolved field description (including range, pattern, etc.)
            violation: optional violation to apply, if None returns valid value

        Return:
            Any: generated value (valid or invalid)
        """
        ...
