from dataclasses import MISSING, dataclass, field, fields

from dataspec.parsing.adapters.dataclass_adapter import (
    parse,
    parse_defaults,
    parse_field,
    parse_fields,
    parse_name,
    supports,
)
from dataspec.specs import FieldSpec, ModelSpec


class NotDataclass:
    pass


@dataclass
class DummyDataclass:
    name: str
    age: int


@dataclass
class DefaultDataclass:
    name: str = field(default="John")
    friends: list = field(default_factory=list)


def test_supports():
    assert supports(DummyDataclass)
    assert not supports(NotDataclass)


def test_parse():
    spec = parse(DummyDataclass)
    assert isinstance(spec, ModelSpec)
    assert spec.name == "DummyDataclass"
    assert spec.type == "dataclass"
    assert isinstance(spec.fields, list)
    assert len(spec.fields) == 2


def test_parse_name():
    assert parse_name(DummyDataclass) == "DummyDataclass"


def test_parse_fields():
    fields = parse_fields(DummyDataclass)
    assert isinstance(fields, list)
    assert len(fields) == 2
    for f in fields:
        assert isinstance(f, FieldSpec)


def test_parse_field():
    field = parse_field(fields(DummyDataclass)[0], str)
    assert isinstance(field, FieldSpec)
    assert field.name == "name"
    assert isinstance(field.type, str)


def test_parse_default():
    default = parse_defaults(fields(DefaultDataclass)[0])
    assert default == "John"


def test_parse_default_factory():
    default = parse_defaults(fields(DefaultDataclass)[1])
    assert default == []


def test_default_missing():
    default = parse_defaults(fields(DummyDataclass)[0])
    assert default == MISSING
