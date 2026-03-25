from typing import Any


class SpecialString(str):
    """Base class for semantic string types"""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "PATTERN" not in cls.__dict__:
            raise TypeError(
                f"Class {cls.__name__} must define class attribute 'PATTERN'"
            )


class Email(SpecialString):
    PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
