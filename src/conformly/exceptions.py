from typing import Any


class ConformlyError(Exception):
    """Base exception for all `conformly` library errors."""

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if not self.context:
            return self.message
        return f"{self.message} | context={self.context}"


class SchemaError(ConformlyError):
    """
    Raised when a schema is invalid, malformed, or contains unsupported constructs.
    """

    pass


class ResolutionError(ConformlyError):
    """
    Raised when the library fails to resolve schema references
    or map types to internal semantics.
    """

    pass


class PlanningError(ConformlyError):
    """
    Raised when a test case cannot be planned due to invalid configuration.
    """


class GenerationError(ConformlyError):
    """
    Raised when synthetic data generation fails or violates internal constraints.
    """

    pass
