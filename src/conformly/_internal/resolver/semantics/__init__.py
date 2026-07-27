from .boolean import BooleanSemantic
from .dict import DictSemantic
from .enum import EnumSemantic
from .list import ListSemantic
from .numeric import NumericSemantic
from .object import ObjectSemantic
from .string import StringSemantic
from .tuple import TupleSemantic
from .uuid import UUIDSemantic

FieldSemantics = (
    NumericSemantic
    | StringSemantic
    | ObjectSemantic
    | BooleanSemantic
    | EnumSemantic
    | ListSemantic
    | UUIDSemantic
    | DictSemantic
    | TupleSemantic
)


__all__ = [
    "BooleanSemantic",
    "DictSemantic",
    "EnumSemantic",
    "FieldSemantics",
    "ListSemantic",
    "NumericSemantic",
    "ObjectSemantic",
    "StringSemantic",
    "TupleSemantic",
    "UUIDSemantic",
]
