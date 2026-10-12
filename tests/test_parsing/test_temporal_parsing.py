from dataclasses import field, make_dataclass
from datetime import date, datetime, time, timedelta
from typing import Annotated

import pytest

from conformly import GreaterOrEqual
from conformly._internal.parser import parse_model


@pytest.mark.parametrize("kind", [date, datetime, time, timedelta])
@pytest.mark.parametrize("source", ["annotated", "metadata", "dict_metadata"])
def test_temporal_types_and_bounds(kind, source):
    bound = kind.min
    if source == "annotated":
        model = make_dataclass(
            "Model", [("value", Annotated[kind, GreaterOrEqual(bound)])]
        )
    elif source == "metadata":
        model = make_dataclass(
            "Model", [("value", kind, field(metadata={"ge": bound}))]
        )
    else:
        model = make_dataclass(
            "Model", [("value", Annotated[kind, {"type": "ge", "value": bound}])]
        )
    element = parse_model(model).fields[0].element
    assert element is not None
    assert element.field_type is kind
    assert element.nested_model is None
    assert element.constraints == (GreaterOrEqual(bound),)
