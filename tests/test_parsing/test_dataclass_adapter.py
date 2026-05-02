from collections.abc import Callable
from dataclasses import InitVar, dataclass, field, fields
from enum import Enum
from typing import Annotated, Any, ClassVar, Literal

import pytest

from conformly._internal.constraints import (
    GreaterOrEqual,
    LessOrEqual,
    MaxLength,
    MinLength,
    OneOf,
)
from conformly._internal.constraints.collections import MaxItems, MinItems, UniqueItems
from conformly._internal.fields import Email
from conformly._internal.parser import FieldSpec, ModelSpec
from conformly._internal.parser.adapters.dataclass import (
    parse,
    parse_defaults,
    parse_field,
    parse_fields,
    resolve_type,
    supports,
)
from conformly._internal.types import ENUMERATED_TYPE, UNSET
from conformly.exceptions import ResolutionError


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


class RoleTypeEnum(Enum):
    admin = 0
    guest = 1
    user = 2


@dataclass
class EnumeratedDataclass:
    role: Literal["admin", "guest", "user"]
    role_type: RoleTypeEnum


@dataclass
class ConstraintsDataclass:
    age: Annotated[int, "ge=0", "le=150"]
    email: Annotated[str, "pattern=^\\w+@\\w+\\.\\w+$"]
    tags: list = field(metadata={"min_length": 1, "max_length": 10})


@dataclass
class MixedDataclass:
    id: int
    name: str = "default"
    email: str | None = None
    age: Annotated[int, "ge=0", "le=150"] = 18


@dataclass
class ListFieldDataclass:
    text: str
    emails: list[Email]
    names: Annotated[
        list[Annotated[str, MinLength(5), MaxLength(15)]], MinItems(2), MaxItems(10)
    ]
    model_list: list[DefaultDataclass]
    unique_list: set[str]


@dataclass
class DictFieldDataclass:
    text: str
    emails: dict[str, Email]
    model_dict: dict[str, DefaultDataclass]
    annotated_dict: Annotated[
        dict[Annotated[str, MinLength(5)], Annotated[str, MaxLength(10)]], MinItems(4)
    ]


class BaseEnum(Enum):
    a = "a"
    b = "b"


# ====== TESTS FOR supports() ======


def test_supports_dataclass() -> None:
    assert supports(DummyDataclass)


def test_supports_not_dataclass() -> None:
    assert not supports(NotDataclass)


def test_supports_int() -> None:
    assert not supports(int)


# ====== TESTS FOR resolve_type() ======


def test_resolve_type_simple() -> None:
    type_hints = {"name": str}
    assert resolve_type(type_hints, "name") is str


def test_resolve_type_int() -> None:
    type_hints = {"age": int}
    assert resolve_type(type_hints, "age") is int


def test_resolve_type_optional() -> None:
    type_hints = {"email": str | None}
    assert resolve_type(type_hints, "email") == str | None


def test_resolve_type_annotated() -> None:
    type_hints = {"age": Annotated[int, "ge=0", "le=150"]}
    field_type = resolve_type(type_hints, "age")
    assert field_type == Annotated[int, "ge=0", "le=150"]


def test_resolve_type_missing_field() -> None:
    type_hints = {"name": str}
    with pytest.raises(KeyError):
        resolve_type(type_hints, "missing_field")


# ====== TESTS FOR parse_defaults() ======


def test_parse_default_simple() -> None:
    default = parse_defaults(fields(DefaultDataclass)[0])
    assert default == "John"


def test_parse_default_factory() -> None:
    default = parse_defaults(fields(DefaultDataclass)[1])
    assert default is list


def test_parse_default_factory_creates_new() -> None:
    factory = parse_defaults(fields(DefaultDataclass)[1])
    first = factory()
    second = factory()
    assert first is not second
    assert first == second


def test_parse_default_missing() -> None:
    default = parse_defaults(fields(DummyDataclass)[0])
    assert default == UNSET


def test_parse_default_none() -> None:
    default = parse_defaults(fields(OptionalDataclass)[0])
    assert default is None
    assert default is not UNSET


def test_parse_default_factory_dict() -> None:
    @dataclass
    class DictDataclass:
        config: dict = field(default_factory=dict)

    default = parse_defaults(fields(DictDataclass)[0])
    assert default is dict
    assert default() == {}


def test_parse_default_zero() -> None:
    @dataclass
    class ZeroDefault:
        count: int = 0

    default = parse_defaults(fields(ZeroDefault)[0])
    assert default == 0
    assert default is not UNSET


def test_parse_default_empty_string() -> None:
    @dataclass
    class EmptyStringDefault:
        text: str = ""

    default = parse_defaults(fields(EmptyStringDefault)[0])
    assert default == ""
    assert default is not UNSET


def test_parse_default_factory_returns_callable() -> None:
    @dataclass
    class CallableDefault:
        fn: Callable = field(default_factory=lambda: len)

    default = parse_defaults(fields(CallableDefault)[0])
    assert callable(default)
    assert default() == len


def test_parse_default_factory_exception() -> None:
    def bad_factory() -> None:
        raise RuntimeError("should not be called during parsing")

    @dataclass
    class BadFactory:
        x: Any = field(default_factory=bad_factory)

    # Should not call factory during parsing
    default = parse_defaults(fields(BadFactory)[0])
    assert default is bad_factory


# ====== TESTS FOR parse_field() ======


def test_parse_field_simple() -> None:
    f = fields(DummyDataclass)[0]
    field_spec = parse_field(f, str)
    assert isinstance(field_spec, FieldSpec)
    assert field_spec.name == "name"
    assert field_spec.element is not None
    assert field_spec.element.field_type is str


def test_parse_field_with_default() -> None:
    f = fields(DefaultDataclass)[0]
    field_spec = parse_field(f, str)
    assert field_spec.default == "John"


def test_parse_field_with_constraints() -> None:
    f = fields(ConstraintsDataclass)[0]
    field_type = Annotated[int, "ge=0", "le=150"]
    field_spec = parse_field(f, field_type)
    assert field_spec.element is not None
    assert len(field_spec.element.constraints) > 0


def test_parse_field_nullable() -> None:
    f = fields(OptionalDataclass)[0]
    field_type = str | None
    field_spec = parse_field(f, field_type)
    assert field_spec.nullable is True


def test_parse_field_not_nullable() -> None:
    f = fields(DummyDataclass)[0]
    field_spec = parse_field(f, str)
    assert field_spec.nullable is False


def test_parse_field_has_default_method() -> None:
    # Field with default
    f1 = fields(DefaultDataclass)[0]
    fs1 = parse_field(f1, str)
    assert fs1.has_default() is True

    f2 = fields(DummyDataclass)[0]
    fs2 = parse_field(f2, str)
    assert fs2.has_default() is False


def test_parse_field_literal() -> None:
    f = fields(EnumeratedDataclass)[0]
    field_spec = parse_field(f, Literal["admin", "guest", "user"])
    assert field_spec.element is not None
    assert field_spec.element.field_type is ENUMERATED_TYPE
    assert len(field_spec.element.constraints) == 1
    assert field_spec.element.constraints[0] == OneOf(("admin", "guest", "user"))


def test_parse_field_enum() -> None:
    f = fields(EnumeratedDataclass)[1]
    field_spec = parse_field(f, RoleTypeEnum)
    assert field_spec.element is not None
    assert field_spec.element.field_type is ENUMERATED_TYPE
    assert len(field_spec.element.constraints) == 1
    assert field_spec.element.constraints[0] == OneOf((0, 1, 2))


# ====== TESTS FOR parse_fields() ======


def test_parse_fields_count() -> None:
    field_specs = parse_fields(DummyDataclass)
    assert len(field_specs) == 2


def test_parse_fields_types() -> None:
    field_specs = parse_fields(DummyDataclass)
    for fs in field_specs:
        assert isinstance(fs, FieldSpec)


def test_parse_fields_names() -> None:
    field_specs = parse_fields(DummyDataclass)
    names = [fs.name for fs in field_specs]
    assert names == ["name", "age"]


def test_parse_fields_mixed() -> None:
    field_specs = parse_fields(MixedDataclass)
    assert len(field_specs) == 4

    assert field_specs[0].name == "id"
    assert field_specs[0].default == UNSET
    assert field_specs[0].nullable is False

    assert field_specs[1].name == "name"
    assert field_specs[1].default == "default"
    assert field_specs[1].nullable is False

    assert field_specs[2].name == "email"
    assert field_specs[2].default is None

    assert field_specs[3].name == "age"
    assert field_specs[3].element is not None
    assert field_specs[3].element.field_type is int
    assert field_specs[3].default == 18
    assert field_specs[3].nullable is False


def test_parse_fields_resolves_types_once() -> None:
    field_specs = parse_fields(DummyDataclass)

    assert all(isinstance(fs.element.field_type, type) for fs in field_specs)  # type: ignore


# ====== TESTS FOR parse() ======


def test_parse_creates_model_spec() -> None:
    spec = parse(DummyDataclass)
    assert isinstance(spec, ModelSpec)


def test_parse_model_name() -> None:
    spec = parse(DummyDataclass)
    assert spec.name == "DummyDataclass"


def test_parse_model_type() -> None:
    spec = parse(DummyDataclass)
    assert spec.type == "dataclass"


def test_parse_model_fields() -> None:
    spec = parse(DummyDataclass)
    assert isinstance(spec.fields, tuple)
    assert len(spec.fields) == 2


def test_parse_mixed_model() -> None:
    spec = parse(MixedDataclass)
    assert spec.name == "MixedDataclass"
    assert len(spec.fields) == 4

    id_field = spec.fields[0]
    assert id_field.name == "id"
    assert id_field.default == UNSET
    assert id_field.has_default() is False


def test_parse_returns_model_spec_attributes() -> None:
    spec = parse(DefaultDataclass)
    assert hasattr(spec, "name")
    assert hasattr(spec, "type")
    assert hasattr(spec, "fields")


def test_parse_ignores_initvar_and_classvar() -> None:
    @dataclass
    class WithSpecialVars:
        normal: str
        init_var: InitVar[int]
        class_var: ClassVar[str] = "shared"

    spec = parse(WithSpecialVars)
    # Only 'normal' should appear
    assert len(spec.fields) == 1
    assert spec.fields[0].name == "normal"


def test_parse_dataclass_with_list_fields() -> None:
    spec = parse(ListFieldDataclass)

    assert len(spec.fields) == 5

    text = spec.fields[0]
    emails = spec.fields[1]
    names = spec.fields[2]
    model_list = spec.fields[3]
    unique_items = spec.fields[4]

    assert text.collection_type is None
    assert emails.item is not None
    assert emails.item.field_type is Email
    assert emails.collection_type is list
    assert len(emails.item.constraints) == 0
    assert names.item is not None
    assert names.item.field_type is str
    assert names.collection_type is list
    assert len(names.item.constraints) == 2
    assert len(names.collection_constraints) == 2
    assert model_list.item is not None
    assert model_list.item.field_type is DefaultDataclass
    assert model_list.item.nested_model is not None
    assert model_list.collection_type is list
    assert unique_items.item is not None
    assert unique_items.item.field_type is str
    assert unique_items.collection_type is set
    assert unique_items.collection_constraints == (UniqueItems(True),)


def test_parse_dataclass_with_dict_fields() -> None:
    spec = parse(DictFieldDataclass)

    assert len(spec.fields) == 4

    text = spec.fields[0]
    emails = spec.fields[1]
    models = spec.fields[2]
    annotated_dicts = spec.fields[3]

    assert text.collection_type is None

    assert emails.collection_type is dict
    assert emails.key is not None
    assert emails.key.field_type is str
    assert emails.value is not None
    assert emails.value.field_type is Email
    assert (
        len(emails.key.constraints)
        == len(emails.value.constraints)
        == len(emails.collection_constraints)
        == 0
    )

    assert models.collection_type is dict
    assert models.key is not None
    assert models.key.field_type is str
    assert models.value is not None
    assert models.value.field_type is DefaultDataclass
    assert models.value.nested_model is not None
    assert (
        len(models.key.constraints)
        == len(models.value.constraints)
        == len(models.collection_constraints)
        == 0
    )

    assert annotated_dicts.collection_type is dict
    assert annotated_dicts.collection_constraints == (MinItems(4),)
    assert annotated_dicts.key is not None
    assert annotated_dicts.key.constraints == (MinLength(5),)
    assert annotated_dicts.value is not None
    assert annotated_dicts.value.constraints == (MaxLength(10),)


# ====== EDGE CASES ======


def test_empty_dataclass() -> None:
    @dataclass
    class EmptyDataclass:
        pass

    spec = parse(EmptyDataclass)
    assert spec.name == "EmptyDataclass"
    assert len(spec.fields) == 0


def test_dataclass_with_only_defaults() -> None:
    @dataclass
    class AllDefaults:
        x: int = 1
        y: str = "default"

    spec = parse(AllDefaults)
    assert all(f.has_default() for f in spec.fields)


def test_dataclass_with_private_fields() -> None:
    @dataclass
    class PrivateFields:
        _private: str = "private"
        public: str = "public"

    spec = parse(PrivateFields)
    assert len(spec.fields) == 2
    assert spec.fields[0].name == "_private"


def test_parse_not_dataclass_raises() -> None:
    with pytest.raises(ResolutionError):
        parse(NotDataclass)


def test_parse_get_field_method() -> None:
    spec = parse(DummyDataclass)
    field = spec.get_field("name")
    assert field.name == "name"
    assert field.element is not None
    assert field.element.field_type is str


def test_parse_get_field_not_found() -> None:
    spec = parse(DummyDataclass)
    with pytest.raises(KeyError):
        spec.get_field("nonexistent")


def test_parse_get_required_fields() -> None:
    spec = parse(MixedDataclass)
    required = spec.get_requiered_fields()
    assert len(required) == 1
    assert required[0].name == "id"


def test_parse_get_optional_fields() -> None:
    spec = parse(MixedDataclass)
    optional = spec.get_optional_fields()
    assert len(optional) == 1
    names = [f.name for f in optional]
    assert "email" in names


# ===== Nested models =====
Name = Annotated[str, MinLength(3), MaxLength(50)]


@dataclass
class Permissions:
    name: Name
    id: int


@dataclass
class Role:
    name: Name
    id: int
    permissions: Permissions


@dataclass
class Group:
    name: Name
    id: int


@dataclass
class User:
    id: int
    name: Name
    age: Annotated[int, GreaterOrEqual(18), LessOrEqual(120)]
    email: Email
    role: Role
    group: Group


def test_parse_nested_models() -> None:
    spec = parse(User)

    assert spec.name == "User"
    assert len(spec.fields) == 6

    role_field = next(f for f in spec.fields if f.name == "role")
    assert role_field.element is not None
    assert role_field.element.nested_model is not None
    assert role_field.element.nested_model.name == "Role"

    permissions_field = next(
        f for f in role_field.element.nested_model.fields if f.name == "permissions"
    )
    assert permissions_field.element is not None
    assert permissions_field.element.nested_model is not None
    assert permissions_field.element.nested_model.name == "Permissions"

    name_field = next(f for f in spec.fields if f.name == "name")
    assert name_field.element is not None
    assert len(name_field.element.constraints) == 2
    assert any(isinstance(c, MinLength) for c in name_field.element.constraints)


def test_parse_is_consistent() -> None:
    spec1 = parse(User)
    spec2 = parse(User)
    assert repr(spec1) == repr(spec2)
