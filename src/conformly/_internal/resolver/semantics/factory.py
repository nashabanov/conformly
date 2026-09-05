from . import FieldSemantics
from .boolean import BooleanSemantic
from .dict import DictSemantic
from .enum import EnumSemantic
from .list import ListSemantic
from .numeric import NumericSemantic
from .object import ObjectSemantic
from .string import StringSemantic
from .tuple import TupleSemantic
from .uuid import UUIDSemantic

from conformly._internal.types import FieldKind, LengthRange, Range


def create_minimal_semantic(kind: FieldKind) -> FieldSemantics:
    match kind:
        case (
            FieldKind.STRING
            | FieldKind.EMAIL
            | FieldKind.IPv4
            | FieldKind.IPv6
            | FieldKind.IPvAny
            | FieldKind.URL
            | FieldKind.HTTPURL
        ):
            return StringSemantic(
                kind=kind, length_range=LengthRange(0, None), pattern=None
            )
        case FieldKind.BOOLEAN:
            return BooleanSemantic()
        case FieldKind.INTEGER:
            return NumericSemantic(
                kind=kind,
                valid_range=Range(0, 100),
                invalid_ranges=(Range(-10, 0), Range(100, 200)),
            )
        case FieldKind.FLOAT:
            return NumericSemantic(
                kind=kind,
                valid_range=Range(0.0, 100.0),
                invalid_ranges=(Range(-10.0, 0), Range(100.0, 200.0)),
            )
        case FieldKind.ENUM:
            return EnumSemantic(values=("__type_mismatch__",))
        case FieldKind.OBJECT:
            return ObjectSemantic()
        case FieldKind.LIST:
            return ListSemantic(
                element_semantic=StringSemantic(
                    kind=FieldKind.STRING,
                    length_range=LengthRange(0, None),
                    pattern=None,
                ),
            )
        case FieldKind.DICT:
            return DictSemantic(
                key_semantic=StringSemantic(
                    kind=FieldKind.STRING,
                    length_range=LengthRange(0, None),
                    pattern=None,
                ),
                value_semantic=NumericSemantic(
                    kind=FieldKind.INTEGER,
                    valid_range=Range(0, 100),
                    invalid_ranges=(Range(-10, 0), Range(100, 110)),
                ),
            )
        case FieldKind.UUID:
            return UUIDSemantic()
        case FieldKind.TUPLE:
            return TupleSemantic(
                elements_semantics=(
                    (
                        StringSemantic(
                            kind=FieldKind.STRING,
                            length_range=LengthRange(0, None),
                            pattern=None,
                        ),
                        None,
                    ),
                ),
                is_variadic=True,
            )
        case _:
            raise ValueError(f"Unsupported FieldKind: {kind}")
