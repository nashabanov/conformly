from .boolean import BooleanSemantic
from .enum import EnumSemantic
from .list import ListSemantic
from .numeric import NumericSemantic
from .object import ObjectSemantic
from .string import StringSemantic

FieldSemantics = (
    NumericSemantic
    | StringSemantic
    | ObjectSemantic
    | BooleanSemantic
    | EnumSemantic
    | ListSemantic
)


__all__ = [
    "BooleanSemantic",
    "EnumSemantic",
    "FieldSemantics",
    "ListSemantic",
    "NumericSemantic",
    "ObjectSemantic",
    "StringSemantic",
]
