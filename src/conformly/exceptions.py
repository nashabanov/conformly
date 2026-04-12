class ConformlyError(Exception):
    """
    Base exception for all library errors.

    Provides structured context for debugging and future serialization.
    """

    pass


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


class InternalError(ConformlyError):
    pass
