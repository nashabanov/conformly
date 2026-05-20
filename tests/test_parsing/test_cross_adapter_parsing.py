import pytest

pytest.importorskip("pydantic", reason="Pydantic adapter requires 'pydantic' package")

from dataclasses import dataclass
from typing import NotRequired, TypedDict

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

    address_field = next(f for f in spec.fields if f.name == "address")

    assert address_field.element is not None
    assert address_field.element.nested_model is not None
    assert len(address_field.element.nested_model.fields) == 2


class AddressTD(TypedDict):
    city: str
    street: str


class UserWithTD(BaseModel):
    name: str
    address: AddressTD


def test_parse_typeddict_in_pydantic_model() -> None:
    spec = parse_model(UserWithTD)

    address_field = next(f for f in spec.fields if f.name == "address")

    assert address_field.element is not None
    nested = address_field.element.nested_model

    assert nested is not None
    assert nested.type == "typeddict"
    assert {f.name for f in nested.fields} == {"city", "street"}


class AddressOptionalTD(TypedDict):
    city: str
    street: NotRequired[str]


class UserWithOptionalTD(BaseModel):
    address: AddressOptionalTD


def test_parse_typeddict_optional_field() -> None:
    spec = parse_model(UserWithOptionalTD)

    assert spec.fields[0].element is not None
    assert spec.fields[0].element.nested_model is not None
    nested = spec.fields[0].element.nested_model
    fields = {f.name: f for f in nested.fields}

    assert fields["city"].default is not None or True
    assert fields["street"].default is None


class InnerModel(BaseModel):
    x: int
    y: int


class OuterModel(BaseModel):
    inner: InnerModel


def test_parse_nested_pydantic_model() -> None:
    spec = parse_model(OuterModel)

    inner_field = spec.fields[0]

    assert inner_field.element is not None
    nested = inner_field.element.nested_model

    assert nested is not None
    assert nested.name == "InnerModel"
    assert len(nested.fields) == 2


class MetaTD(TypedDict):
    version: int


@dataclass
class Profile:
    meta: MetaTD


class ComplexUser(BaseModel):
    profile: Profile


def test_parse_deep_mixed_nesting() -> None:
    spec = parse_model(ComplexUser)

    assert spec.fields[0].element is not None
    assert spec.fields[0].element.nested_model is not None

    profile_model = spec.fields[0].element.nested_model

    assert profile_model is not None

    assert profile_model.fields[0].element is not None
    assert profile_model.fields[0].element.nested_model is not None

    meta_model = profile_model.fields[0].element.nested_model

    assert meta_model is not None
    assert meta_model.type == "typeddict"
    assert {f.name for f in meta_model.fields} == {"version"}
