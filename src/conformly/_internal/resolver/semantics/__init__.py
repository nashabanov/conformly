from .boolean import BooleanSemantic
from .enum import EnumSemantic
from .list import ListSemantic
from .numeric import NumericSemantic
from .object import ObjectSemantic
from .string import StringSemantic
from .uuid import UUIDSemantic

FieldSemantics = (
    NumericSemantic
    | StringSemantic
    | ObjectSemantic
    | BooleanSemantic
    | EnumSemantic
    | ListSemantic
    | UUIDSemantic
)


__all__ = [
    "BooleanSemantic",
    "EnumSemantic",
    "FieldSemantics",
    "ListSemantic",
    "NumericSemantic",
    "ObjectSemantic",
    "StringSemantic",
    "UUIDSemantic",
]
