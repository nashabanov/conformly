import pytest

from conformly import GreaterThan, MaxLength, MinLength, Pattern
from conformly._internal.resolver.semantics.bytes import create_bytes_semantic
from conformly._internal.types import FieldKind, LengthRange
from conformly.exceptions import SchemaError


@pytest.mark.parametrize(
    "constraints,expected",
    [
        ((), LengthRange(0, None)),
        ((MinLength(5),), LengthRange(5, None)),
        ((MaxLength(0),), LengthRange(0, 0)),
        ((MinLength(1), MinLength(3), MaxLength(8), MaxLength(5)), LengthRange(3, 5)),
    ],
)
def test_bytes_length_intersection(constraints, expected):
    semantic = create_bytes_semantic(constraints)
    assert semantic.kind is FieldKind.BYTES
    assert semantic.length_range == expected
    assert semantic.has_constraints == bool(constraints)


@pytest.mark.parametrize(
    "constraints",
    [
        (MinLength(1), MaxLength(0)),
        (MinLength(-1),),
        (MaxLength(-1),),
        (MinLength(True),),
        (MaxLength(1.5),),
        (Pattern(".*"),),
        (GreaterThan(1),),
    ],
)
def test_invalid_bytes_constraints_rejected(constraints):
    with pytest.raises(SchemaError):
        create_bytes_semantic(constraints)
