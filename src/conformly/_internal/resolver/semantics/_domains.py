from typing import Any

from . import BooleanSemantic, EnumSemantic, FieldSemantics, NumericSemantic

from conformly._internal.types import FieldKind


def finite_cardinality(semantic: FieldSemantics) -> int | None:
    if isinstance(semantic, BooleanSemantic):
        return 2
    if isinstance(semantic, EnumSemantic):
        # Equality, rather than type or identity, determines collection uniqueness.
        values: list[Any] = []
        for value in semantic.values:
            if value not in values:
                values.append(value)
        return len(values)
    if isinstance(semantic, NumericSemantic) and semantic.kind == FieldKind.INTEGER:
        lower = int(semantic.valid_range.min_value)
        upper = int(semantic.valid_range.max_value)
        step = int(semantic.multiple_of) if semantic.multiple_of is not None else 1
        if step > 0:
            return max(0, upper // step - (lower - 1) // step)
    return None
