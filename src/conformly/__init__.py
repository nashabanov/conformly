from ._internal.parser.adapters.bootstrap import register_builtin_adapters

register_builtin_adapters()

# ruff: noqa: E402
from ._internal.api import case, cases, path
from ._internal.constraints import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxItems,
    MaxLength,
    MinItems,
    MinLength,
    MultipleOf,
    OneOf,
    Pattern,
    UniqueItems,
)
from ._internal.fields import Email, IPv4, IPv6, IPvAny
from ._internal.types import ViolationType as V
from .exceptions import ConformlyError

__all__ = [
    "ConformlyError",
    "Email",
    "GreaterOrEqual",
    "GreaterThan",
    "IPv4",
    "IPv6",
    "IPvAny",
    "LessOrEqual",
    "LessThan",
    "MaxItems",
    "MaxLength",
    "MinItems",
    "MinLength",
    "MultipleOf",
    "OneOf",
    "Pattern",
    "UniqueItems",
    "V",
    "case",
    "cases",
    "path",
]
