from typing import Any


class ConformlyError(Exception):
    """
    Base exception for all library errors.
    """

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if not self.context:
            return self.message
        return f"{self.message} | context={self.context}"


class SchemaError(ConformlyError):
    pass


class ResolutionError(ConformlyError):
    pass


class PlanningError(ConformlyError):
    pass


class GenerationError(ConformlyError):
    pass


class ViolationError(ConformlyError):
    pass
