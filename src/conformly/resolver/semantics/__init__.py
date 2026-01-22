from .numeric import NumericSemantic
from .string import StringSemantic

FieldSemantics = NumericSemantic | StringSemantic


__all__ = ["FieldSemantics", "NumericSemantic", "StringSemantic"]
