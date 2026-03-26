class SpecialString(str):
    """Base class for semantic string types"""

    PATTERN = ""


class Email(SpecialString):
    PATTERN = (
        r"^[a-zA-Z0-9](\.?[a-zA-Z0-9_+%+-])*@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])"
        r"?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,63}$"
    )
