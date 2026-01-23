from .boolean import BooleanSemantic
from .numeric import NumericSemantic
from .object import ObjectSemantic
from .string import StringSemantic

FieldSemantics = NumericSemantic | StringSemantic | ObjectSemantic | BooleanSemantic


__all__ = [
    "BooleanSemantic",
    "FieldSemantics",
    "NumericSemantic",
    "ObjectSemantic",
    "StringSemantic",
]
