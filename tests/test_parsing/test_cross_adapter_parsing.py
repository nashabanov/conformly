import pytest

pytest.importorskip("pydantic", reason="Pydantic adapter requires 'pydantic' package")

from dataclasses import dataclass

from pydantic import BaseModel

from conformly._internal.parser import parse_model


@dataclass
class Address:
    city: str
    street: str


class User(BaseModel):
    name: str
    address: Address


def test_parse_dataclass_in_pydantic_model() -> None:
    spec = parse_model(User)

    assert len(spec.fields) == 2
    assert spec.fields[1].element is not None
    assert spec.fields[1].element.nested_model is not None
    assert len(spec.fields[1].element.nested_model.fields) == 2
