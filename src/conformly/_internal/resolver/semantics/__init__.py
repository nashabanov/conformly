from .boolean import BooleanSemantic
from .bytes import BytesSemantic
from .dict import DictSemantic
from .enum import EnumSemantic
from .list import ListSemantic
from .numeric import NumericSemantic
from .object import ObjectSemantic
from .string import StringSemantic
from .temporal import TemporalSemantic
from .tuple import TupleSemantic
from .uuid import UUIDSemantic

FieldSemantics = (
    NumericSemantic
    | StringSemantic
    | BytesSemantic
    | ObjectSemantic
    | BooleanSemantic
    | EnumSemantic
    | ListSemantic
    | UUIDSemantic
    | DictSemantic
    | TemporalSemantic
    | TupleSemantic
)


__all__ = [
    "BooleanSemantic",
    "BytesSemantic",
    "DictSemantic",
    "EnumSemantic",
    "FieldSemantics",
    "ListSemantic",
    "NumericSemantic",
    "ObjectSemantic",
    "StringSemantic",
    "TemporalSemantic",
    "TupleSemantic",
    "UUIDSemantic",
]
