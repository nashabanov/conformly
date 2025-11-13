from dataclasses import dataclass, field, fields
from typing import Annotated

import pytest

from dataspec.parsing.adapters.dataclass_adapter import (
    is_nullable,
    parse,
    parse_annotated_constraints,
    parse_constraints,
    parse_defaults,
    parse_field,
    parse_fields,
    parse_metadata_constraints,
    parse_name,
    resolve_type,
    supports,
)
from dataspec.specs import FieldSpec, ModelSpec
from dataspec.specs.field import _UNSET


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


@dataclass
class OptionalDataclass:
    email: str | None = None
    nickname: int | None = None


@dataclass
class ConstraintsDataclass:
    age: Annotated[int, "min=0", "max=150"]
    email: Annotated[str, "pattern=^\\w+@\\w+\\.\\w+$"]
    tags: list = field(metadata={"min": 1, "max": 10})


@dataclass
class MixedDataclass:
    id: int
    name: str = "default"
    email: str | None = None
    age: Annotated[int, "min=0", "max=150"] = 18


# ====== TESTS FOR supports() ======


def test_supports_dataclass():
    assert supports(DummyDataclass)


def test_supports_not_dataclass():
    assert not supports(NotDataclass)


def test_supports_int():
    assert not supports(int)


# ====== TESTS FOR parse_name() ======


def test_parse_name():
    assert parse_name(DummyDataclass) == "DummyDataclass"


def test_parse_name_complex():
    assert parse_name(OptionalDataclass) == "OptionalDataclass"


def test_parse_name_constraints():
    assert parse_name(ConstraintsDataclass) == "ConstraintsDataclass"


# ====== TESTS FOR resolve_type() ======


def test_resolve_type_simple():
    type_hints = {"name": str}
    assert resolve_type(type_hints, "name") is str


def test_resolve_type_int():
    type_hints = {"age": int}
    assert resolve_type(type_hints, "age") is int


def test_resolve_type_optional():
    type_hints = {"email": str | None}
    assert resolve_type(type_hints, "email") == str | None


def test_resolve_type_annotated():
    type_hints = {"age": Annotated[int, "min=0", "max=150"]}
    field_type = resolve_type(type_hints, "age")
    assert field_type == Annotated[int, "min=0", "max=150"]


def test_resolve_type_missing_field():
    type_hints = {"name": str}
    with pytest.raises(KeyError):
        resolve_type(type_hints, "missing_field")


# ====== TESTS FOR is_nullable() ======


def test_is_nullable_optional_str():
    assert is_nullable(str | None)


def test_is_nullable_optional_int():
    assert is_nullable(int | None)


def test_is_nullable_union_with_none():
    assert is_nullable(str | None)


def test_is_nullable_union_multiple_with_none():
    assert is_nullable(str | int | None)


def test_is_nullable_not_optional_str():
    assert not is_nullable(str)


def test_is_nullable_not_optional_int():
    assert not is_nullable(int)


def test_is_nullable_union_without_none():
    assert not is_nullable(str | int)


def test_is_nullable_list():
    assert not is_nullable(list)


# ====== TESTS FOR parse_defaults() ======


def test_parse_default_simple():
    default = parse_defaults(fields(DefaultDataclass)[0])
    assert default == "John"


def test_parse_default_factory():
    default = parse_defaults(fields(DefaultDataclass)[1])
    assert default == []


def test_parse_default_factory_creates_new():
    first = parse_defaults(fields(DefaultDataclass)[1])
    second = parse_defaults(fields(DefaultDataclass)[1])
    assert first is not second
    assert first == second


def test_parse_default_missing():
    default = parse_defaults(fields(DummyDataclass)[0])
    assert default == _UNSET


def test_parse_default_none():
    default = parse_defaults(fields(OptionalDataclass)[0])
    assert default is None
    assert default is not _UNSET


def test_parse_default_factory_dict():
    @dataclass
    class DictDataclass:
        config: dict = field(default_factory=dict)

    default = parse_defaults(fields(DictDataclass)[0])
    assert default == {}


def test_parse_default_zero():
    @dataclass
    class ZeroDefault:
        count: int = 0

    default = parse_defaults(fields(ZeroDefault)[0])
    assert default == 0
    assert default is not _UNSET


def test_parse_default_empty_string():
    @dataclass
    class EmptyStringDefault:
        text: str = ""

    default = parse_defaults(fields(EmptyStringDefault)[0])
    assert default == ""
    assert default is not _UNSET


# ====== TESTS FOR parse_annotated_constraints() ======


def test_parse_annotated_constraints_exists():
    constraints = parse_annotated_constraints(Annotated[int, "min=0", "max=150"])
    assert len(constraints) == 2
    # TODO: Verify ConstraintSpec objects


def test_parse_annotated_constraints_empty():
    constraints = parse_annotated_constraints(str)
    assert constraints == []


def test_parse_annotated_constraints_single():
    constraints = parse_annotated_constraints(Annotated[str, "pattern=^\\w+$"])
    assert len(constraints) == 1


def test_parse_annotated_constraints_none():
    constraints = parse_annotated_constraints(type(None))
    assert constraints == []


# ====== TESTS FOR parse_metadata_constraints() ======


def test_parse_metadata_constraints_exists():
    f = fields(ConstraintsDataclass)[2]  # tags field
    constraints = parse_metadata_constraints(f)
    assert len(constraints) > 0
    # TODO: Verify ConstraintSpec objects


def test_parse_metadata_constraints_empty():
    f = fields(DummyDataclass)[0]
    constraints = parse_metadata_constraints(f)
    assert constraints == []


def test_parse_metadata_constraints_custom_keys():
    @dataclass
    class CustomMetadata:
        value: int = field(metadata={"custom_key": "custom_value"})

    f = fields(CustomMetadata)[0]
    with pytest.raises(ValueError):
        parse_metadata_constraints(f)


# ====== TESTS FOR parse_constraints() ======


def test_parse_constraints_combined():
    f = fields(ConstraintsDataclass)[0]  # age with Annotated
    field_type = Annotated[int, "min=0", "max=150"]
    constraints = parse_constraints(f, field_type)
    assert len(constraints) > 0


def test_parse_constraints_annotated_only():
    f = fields(DummyDataclass)[0]
    field_type = Annotated[str, "min=3"]
    constraints = parse_constraints(f, field_type)
    assert len(constraints) >= 1


def test_parse_constraints_metadata_only():
    f = fields(ConstraintsDataclass)[2]  # tags field with metadata
    field_type = list
    constraints = parse_constraints(f, field_type)
    assert len(constraints) > 0


def test_parse_constraints_no_constraints():
    f = fields(DummyDataclass)[0]
    constraints = parse_constraints(f, str)
    assert constraints == []


# ====== TESTS FOR parse_field() ======


def test_parse_field_simple():
    f = fields(DummyDataclass)[0]
    field_spec = parse_field(f, str)
    assert isinstance(field_spec, FieldSpec)
    assert field_spec.name == "name"
    assert field_spec.type is str


def test_parse_field_with_default():
    f = fields(DefaultDataclass)[0]
    field_spec = parse_field(f, str)
    assert field_spec.default == "John"


def test_parse_field_with_constraints():
    f = fields(ConstraintsDataclass)[0]
    field_type = Annotated[int, "min=0", "max=150"]
    field_spec = parse_field(f, field_type)
    assert len(field_spec.constraints) > 0


def test_parse_field_nullable():
    f = fields(OptionalDataclass)[0]
    field_type = str | None
    field_spec = parse_field(f, field_type)
    assert field_spec.nullable is True


def test_parse_field_not_nullable():
    f = fields(DummyDataclass)[0]
    field_spec = parse_field(f, str)
    assert field_spec.nullable is False


def test_parse_field_has_default_method():
    # Field with default
    f1 = fields(DefaultDataclass)[0]
    fs1 = parse_field(f1, str)
    assert fs1.has_default() is True

    f2 = fields(DummyDataclass)[0]
    fs2 = parse_field(f2, str)
    assert fs2.has_default() is False


# ====== TESTS FOR parse_fields() ======


def test_parse_fields_count():
    field_specs = parse_fields(DummyDataclass)
    assert len(field_specs) == 2


def test_parse_fields_types():
    field_specs = parse_fields(DummyDataclass)
    for fs in field_specs:
        assert isinstance(fs, FieldSpec)


def test_parse_fields_names():
    field_specs = parse_fields(DummyDataclass)
    names = [fs.name for fs in field_specs]
    assert names == ["name", "age"]


def test_parse_fields_mixed():
    field_specs = parse_fields(MixedDataclass)
    assert len(field_specs) == 4

    assert field_specs[0].name == "id"
    assert field_specs[0].default == _UNSET
    assert field_specs[0].nullable is False

    assert field_specs[1].name == "name"
    assert field_specs[1].default == "default"
    assert field_specs[1].nullable is False

    assert field_specs[2].name == "email"
    assert field_specs[2].default is None

    assert field_specs[3].name == "age"
    assert field_specs[3].default == 18
    assert field_specs[3].nullable is False


def test_parse_fields_resolves_types_once():
    field_specs = parse_fields(DummyDataclass)

    assert all(isinstance(fs.type, type) for fs in field_specs)


# ====== TESTS FOR parse() ======


def test_parse_creates_model_spec():
    spec = parse(DummyDataclass)
    assert isinstance(spec, ModelSpec)


def test_parse_model_name():
    spec = parse(DummyDataclass)
    assert spec.name == "DummyDataclass"


def test_parse_model_type():
    spec = parse(DummyDataclass)
    assert spec.type == "dataclass"


def test_parse_model_fields():
    spec = parse(DummyDataclass)
    assert isinstance(spec.fields, list)
    assert len(spec.fields) == 2


def test_parse_mixed_model():
    spec = parse(MixedDataclass)
    assert spec.name == "MixedDataclass"
    assert len(spec.fields) == 4

    id_field = spec.fields[0]
    assert id_field.name == "id"
    assert id_field.default == _UNSET
    assert id_field.has_default() is False


def test_parse_returns_model_spec_attributes():
    spec = parse(DefaultDataclass)
    assert hasattr(spec, "name")
    assert hasattr(spec, "type")
    assert hasattr(spec, "fields")


# ====== EDGE CASES ======


def test_empty_dataclass():
    @dataclass
    class EmptyDataclass:
        pass

    spec = parse(EmptyDataclass)
    assert spec.name == "EmptyDataclass"
    assert len(spec.fields) == 0


def test_dataclass_with_only_defaults():
    @dataclass
    class AllDefaults:
        x: int = 1
        y: str = "default"

    spec = parse(AllDefaults)
    assert all(f.has_default() for f in spec.fields)


def test_dataclass_with_private_fields():
    @dataclass
    class PrivateFields:
        _private: str = "private"
        public: str = "public"

    spec = parse(PrivateFields)
    assert len(spec.fields) == 2
    assert spec.fields[0].name == "_private"


def test_parse_not_dataclass_raises():
    with pytest.raises(TypeError):
        parse(NotDataclass)


def test_parse_get_field_method():
    spec = parse(DummyDataclass)
    field = spec.get_field("name")
    assert field.name == "name"
    assert field.type is str


def test_parse_get_field_not_found():
    spec = parse(DummyDataclass)
    with pytest.raises(KeyError):
        spec.get_field("nonexistent")


def test_parse_get_required_fields():
    spec = parse(MixedDataclass)
    required = spec.get_requiered_fields()
    assert len(required) == 1
    assert required[0].name == "id"


def test_parse_get_optional_fields():
    spec = parse(MixedDataclass)
    optional = spec.get_optional_fields()
    assert len(optional) == 3
    names = [f.name for f in optional]
    assert "name" in names
    assert "email" in names
    assert "age" in names
