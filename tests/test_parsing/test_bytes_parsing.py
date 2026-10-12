from dataclasses import field, make_dataclass
from typing import Annotated, TypedDict

from conformly import MaxLength, MinLength
from conformly._internal.parser import parse_model


def test_bytes_annotated_and_metadata_constraints():
    model = make_dataclass(
        "Payload",
        [
            ("annotated", Annotated[bytes, MinLength(2), MaxLength(5)]),
            ("metadata", bytes, field(metadata={"min_length": 2, "max_length": 5})),
        ],
    )
    for spec in parse_model(model).fields:
        assert spec.element is not None
        assert spec.element.field_type is bytes
        assert spec.element.nested_model is None
        assert spec.element.constraints == (MinLength(2), MaxLength(5))


def test_optional_bytes_typeddict():
    class Payload(TypedDict):
        value: Annotated[bytes | None, MaxLength(5)]

    spec = parse_model(Payload).fields[0]
    assert spec.nullable
    assert spec.element is not None
    assert spec.element.field_type is bytes
    assert spec.element.constraints == (MaxLength(5),)
