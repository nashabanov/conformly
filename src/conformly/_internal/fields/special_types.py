class SpecialString(str):
    """Base class for semantic string types"""

    pass


class Email(SpecialString):
    pass


class IPv4(SpecialString):
    pass


class IPv6(SpecialString):
    pass


class IPvAny(SpecialString):
    pass
