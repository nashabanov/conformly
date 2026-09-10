from typing import Literal

from conformly._internal.resolver.semantics import (
    FieldSemantics,
    ListSemantic,
    NumericSemantic,
    StringSemantic,
)
from conformly._internal.types import (
    INT_MAX,
    INT_MIN,
    FieldKind,
    LengthRange,
    Range,
)


def string_semantic(
    *,
    kind: FieldKind = FieldKind.STRING,
    min_length: int = 5,
    max_length: int | None = 15,
    pattern: str | None = r"/\d+/",
    has_constraints: bool = True,
) -> StringSemantic:
    return StringSemantic(
        kind=kind,
        length_range=LengthRange(min_length, max_length),
        pattern=pattern,
        has_constraints=has_constraints,
    )


def numeric_semantic(
    *,
    kind: Literal[FieldKind.INTEGER, FieldKind.FLOAT] = FieldKind.INTEGER,
    valid_range: Range = Range(2, 10),
    invalid_ranges: tuple[Range, ...] = (
        Range(INT_MIN, 1),
        Range(11, INT_MAX),
    ),
    has_constraints: bool = True,
) -> NumericSemantic:
    return NumericSemantic(
        kind=kind,
        valid_range=valid_range,
        invalid_ranges=invalid_ranges,
        has_constraints=has_constraints,
    )


def list_semantic(
    element_semantic: FieldSemantics,
    *,
    has_constraints: bool = False,
) -> ListSemantic:
    return ListSemantic(
        element_semantic=element_semantic,
        has_constraints=has_constraints,
    )
