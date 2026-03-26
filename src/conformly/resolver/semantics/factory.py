from ...types import FieldKind, LengthRange, Range
from ..semantics import FieldSemantics
from .boolean import BooleanSemantic
from .enum import EnumSemantic
from .numeric import NumericSemantic
from .object import ObjectSemantic
from .string import StringSemantic


def create_minimal_semantic(kind: FieldKind) -> FieldSemantics:
    match kind:
        case FieldKind.STRING:
            return StringSemantic(kind, LengthRange(0, None), None, False)
        case FieldKind.BOOLEAN:
            return BooleanSemantic(kind)
        case FieldKind.INTEGER:
            return NumericSemantic(
                kind, Range(0, 100), (Range(-10, 0), Range(100, 200)), False
            )
        case FieldKind.FLOAT:
            return NumericSemantic(
                kind, Range(0.0, 100.0), (Range(-10.0, 0), Range(100.0, 200.0)), False
            )
        case FieldKind.ENUM:
            return EnumSemantic(kind, ("__type_mismatch__",), False)
        case FieldKind.OBJECT:
            return ObjectSemantic(kind)
        case FieldKind.EMAIL:
            return StringSemantic(kind, LengthRange(0, None), None, False)
        case _:
            raise ValueError(f"Unsupported FieldKind: {kind}")
