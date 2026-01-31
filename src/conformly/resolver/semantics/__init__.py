from .boolean import BooleanSemantic
from .enum import EnumSemantic
from .numeric import NumericSemantic
from .object import ObjectSemantic
from .string import StringSemantic

FieldSemantics = (
    NumericSemantic | StringSemantic | ObjectSemantic | BooleanSemantic | EnumSemantic
)


__all__ = [
    "BooleanSemantic",
    "EnumSemantic",
    "FieldSemantics",
    "NumericSemantic",
    "ObjectSemantic",
    "StringSemantic",
]
