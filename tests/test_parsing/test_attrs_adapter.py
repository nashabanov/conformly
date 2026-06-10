import pytest

pytest.importorskip("attrs", reason="attrs adapter requires 'attrs' package")

from enum import Enum
from typing import Annotated, Any, Literal

import attrs

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
from conformly._internal.parser.adapters.attrs import (
    parse,
    parse_defaults,
    parse_field,
    parse_fields,
    resolve_type,
    supports,
)
from conformly._internal.types import ENUMERATED_TYPE, UNSET
from conformly.exceptions import ResolutionError

# ====== FIXTURES & MODELS ======


class NotAttrs:
    pass


@attrs.define
class DummyAttrs:
    x: int
    y: str


@attrs.define
class DefaultAttrs:
    name: str = attrs.field(default="John")
    items: list = attrs.field(factory=list)


@attrs.define
class OptionalAttrs:
    email: str | None = None
    nickname: int | None = None


class RoleTypeEnum(Enum):
    admin = 0
    guest = 1
    user = 2


@attrs.define
class EnumeratedAttrs:
    role: Literal["admin", "guest", "user"]
    role_type: RoleTypeEnum


@attrs.define
class ConstraintsAttrs:
    # Constraints только через Annotated, как указано в требованиях
    age: Annotated[int, "ge=0", "le=150"]
    email: Annotated[str, "pattern=^\\w+@\\w+\\.\\w+$"]
    tags: Annotated[list[str], MinItems(1), MaxItems(10)]


@attrs.define
class MixedAttrs:
    id: int
    name: str = "default"
    email: str | None = None
    age: Annotated[int, "ge=0", "le=150"] = 18


@attrs.define
class ListFieldAttrs:
    text: str
    emails: list[Email]
    names: Annotated[
        list[Annotated[str, MinLength(5), MaxLength(15)]], MinItems(2), MaxItems(10)
    ]
    model_list: list[DefaultAttrs]
    unique_list: set[str]


@attrs.define
class DictFieldAttrs:
    text: str
    emails: dict[str, Email]
    model_dict: dict[str, DefaultAttrs]
    annotated_dict: Annotated[
        dict[Annotated[str, MinLength(5)], Annotated[str, MaxLength(10)]], MinItems(4)
    ]


# ====== TESTS FOR supports() ======


def test_supports_attrs() -> None:
    assert supports(DummyAttrs)


def test_supports_not_attrs() -> None:
    assert not supports(NotAttrs)


def test_supports_int() -> None:
    assert not supports(int)


def test_supports_legacy_attrs() -> None:
    import attr

    @attr.s
    class LegacyAttrs:
        x: int

    assert supports(LegacyAttrs)


# ====== TESTS FOR resolve_type() ======


def test_resolve_type_simple() -> None:
    type_hints = {"x": int}
    assert resolve_type(type_hints, "x") is int


def test_resolve_type_optional() -> None:
    type_hints = {"email": str | None}
    assert resolve_type(type_hints, "email") == str | None


def test_resolve_type_annotated() -> None:
    type_hints = {"age": Annotated[int, "ge=0", "le=150"]}
    field_type = resolve_type(type_hints, "age")
    assert field_type == Annotated[int, "ge=0", "le=150"]


# ====== TESTS FOR parse_defaults() ======


def test_parse_default_simple() -> None:
    fields = attrs.fields(DefaultAttrs)
    default = parse_defaults(fields[0])
    assert default == "John"


def test_parse_default_factory() -> None:
    fields = attrs.fields(DefaultAttrs)
    default = parse_defaults(fields[1])
    assert default.factory is list


def test_parse_default_factory_creates_new() -> None:
    fields = attrs.fields(DefaultAttrs)
    factory_obj = parse_defaults(fields[1])
    first = factory_obj.factory()
    second = factory_obj.factory()
    assert first is not second
    assert first == second


def test_parse_default_missing() -> None:
    fields = attrs.fields(DummyAttrs)
    default = parse_defaults(fields[0])
    assert default == UNSET


def test_parse_default_none() -> None:
    fields = attrs.fields(OptionalAttrs)
    default = parse_defaults(fields[0])
    assert default is None
    assert default is not UNSET


def test_parse_default_zero() -> None:
    @attrs.define
    class ZeroDefault:
        count: int = 0

    default = parse_defaults(attrs.fields(ZeroDefault)[0])
    assert default == 0
    assert default is not UNSET


def test_parse_default_empty_string() -> None:
    @attrs.define
    class EmptyStringDefault:
        text: str = ""

    default = parse_defaults(attrs.fields(EmptyStringDefault)[0])
    assert default == ""
    assert default is not UNSET


def test_parse_default_factory_exception() -> None:
    def bad_factory() -> None:
        raise RuntimeError("should not be called during parsing")

    @attrs.define
    class BadFactory:
        x: Any = attrs.field(factory=bad_factory)

    default = parse_defaults(attrs.fields(BadFactory)[0])
    assert default.factory is bad_factory


# ====== TESTS FOR parse_field() ======


def test_parse_field_simple() -> None:
    f = attrs.fields(DummyAttrs)[0]
    field_spec = parse_field(f, int)
    assert isinstance(field_spec, FieldSpec)
    assert field_spec.name == "x"
    assert field_spec.element is not None
    assert field_spec.element.field_type is int


def test_parse_field_with_default() -> None:
    f = attrs.fields(DefaultAttrs)[0]
    field_spec = parse_field(f, str)
    assert field_spec.default == "John"


def test_parse_field_with_constraints() -> None:
    f = attrs.fields(ConstraintsAttrs)[0]
    field_type = Annotated[int, "ge=0", "le=150"]
    field_spec = parse_field(f, field_type)
    assert field_spec.element is not None
    assert len(field_spec.element.constraints) > 0


def test_parse_field_nullable() -> None:
    f = attrs.fields(OptionalAttrs)[0]
    field_type = str | None
    field_spec = parse_field(f, field_type)
    assert field_spec.nullable is True


def test_parse_field_not_nullable() -> None:
    f = attrs.fields(DummyAttrs)[0]
    field_spec = parse_field(f, int)
    assert field_spec.nullable is False


def test_parse_field_has_default_method() -> None:
    f1 = attrs.fields(DefaultAttrs)[0]
    fs1 = parse_field(f1, str)
    assert fs1.has_default() is True

    f2 = attrs.fields(DummyAttrs)[0]
    fs2 = parse_field(f2, int)
    assert fs2.has_default() is False


def test_parse_field_literal() -> None:
    f = attrs.fields(EnumeratedAttrs)[0]
    field_spec = parse_field(f, Literal["admin", "guest", "user"])
    assert field_spec.element is not None
    assert field_spec.element.field_type is ENUMERATED_TYPE
    assert len(field_spec.element.constraints) == 1
    assert field_spec.element.constraints[0] == OneOf(("admin", "guest", "user"))


def test_parse_field_enum() -> None:
    f = attrs.fields(EnumeratedAttrs)[1]
    field_spec = parse_field(f, RoleTypeEnum)
    assert field_spec.element is not None
    assert field_spec.element.field_type is ENUMERATED_TYPE
    assert len(field_spec.element.constraints) == 1
    assert field_spec.element.constraints[0] == OneOf((0, 1, 2))


# ====== TESTS FOR parse_fields() ======


def test_parse_fields_count() -> None:
    field_specs = parse_fields(DummyAttrs)
    assert len(field_specs) == 2


def test_parse_fields_types() -> None:
    field_specs = parse_fields(DummyAttrs)
    for fs in field_specs:
        assert isinstance(fs, FieldSpec)


def test_parse_fields_names() -> None:
    field_specs = parse_fields(DummyAttrs)
    names = [fs.name for fs in field_specs]
    assert names == ["x", "y"]


def test_parse_fields_mixed() -> None:
    field_specs = parse_fields(MixedAttrs)
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


# ====== TESTS FOR parse() ======


def test_parse_creates_model_spec() -> None:
    spec = parse(DummyAttrs)
    assert isinstance(spec, ModelSpec)


def test_parse_model_name() -> None:
    spec = parse(DummyAttrs)
    assert spec.name == "DummyAttrs"


def test_parse_model_type() -> None:
    spec = parse(DummyAttrs)
    assert spec.type == "attrs"


def test_parse_model_fields() -> None:
    spec = parse(DummyAttrs)
    assert isinstance(spec.fields, tuple)
    assert len(spec.fields) == 2


def test_parse_mixed_model() -> None:
    spec = parse(MixedAttrs)
    assert spec.name == "MixedAttrs"
    assert len(spec.fields) == 4

    id_field = spec.fields[0]
    assert id_field.name == "id"
    assert id_field.default == UNSET
    assert id_field.has_default() is False


def test_parse_not_attrs_raises() -> None:
    with pytest.raises(ResolutionError):
        parse(NotAttrs)


def test_parse_get_field_method() -> None:
    spec = parse(DummyAttrs)
    field = spec.get_field("x")
    assert field.name == "x"
    assert field.element is not None
    assert field.element.field_type is int


def test_parse_get_field_not_found() -> None:
    spec = parse(DummyAttrs)
    with pytest.raises(KeyError):
        spec.get_field("nonexistent")


def test_parse_get_required_fields() -> None:
    spec = parse(MixedAttrs)
    required = spec.get_requiered_fields()
    assert len(required) == 1
    assert required[0].name == "id"


def test_parse_get_optional_fields() -> None:
    spec = parse(MixedAttrs)
    optional = spec.get_optional_fields()
    assert len(optional) == 1
    names = [f.name for f in optional]
    assert "email" in names


# ====== EDGE CASES ======


def test_empty_attrs() -> None:
    @attrs.define
    class EmptyAttrs:
        pass

    spec = parse(EmptyAttrs)
    assert spec.name == "EmptyAttrs"
    assert len(spec.fields) == 0


def test_attrs_with_only_defaults() -> None:
    @attrs.define
    class AllDefaults:
        x: int = 1
        y: str = "default"

    spec = parse(AllDefaults)
    assert all(f.has_default() for f in spec.fields)


def test_attrs_with_private_fields() -> None:
    @attrs.define
    class PrivateFields:
        _private: str = "private"
        public: str = "public"

    spec = parse(PrivateFields)
    assert len(spec.fields) == 2
    assert spec.fields[0].name == "_private"


def test_parse_is_consistent() -> None:
    spec1 = parse(MixedAttrs)
    spec2 = parse(MixedAttrs)
    assert spec1 is spec2


# ===== Nested models ======
Name = Annotated[str, MinLength(3), MaxLength(50)]


@attrs.define
class PermissionsAttrs:
    name: Name
    id: int


@attrs.define
class RoleAttrs:
    name: Name
    id: int
    permissions: PermissionsAttrs


@attrs.define
class GroupAttrs:
    name: Name
    id: int


@attrs.define
class UserAttrs:
    id: int
    name: Name
    age: Annotated[int, GreaterOrEqual(18), LessOrEqual(120)]
    email: Email
    role: RoleAttrs
    group: GroupAttrs


def test_parse_nested_models() -> None:
    spec = parse(UserAttrs)

    assert spec.name == "UserAttrs"
    assert len(spec.fields) == 6

    role_field = next(f for f in spec.fields if f.name == "role")
    assert role_field.element is not None
    assert role_field.element.nested_model is not None
    assert role_field.element.nested_model.name == "RoleAttrs"

    permissions_field = next(
        f for f in role_field.element.nested_model.fields if f.name == "permissions"
    )
    assert permissions_field.element is not None
    assert permissions_field.element.nested_model is not None
    assert permissions_field.element.nested_model.name == "PermissionsAttrs"

    name_field = next(f for f in spec.fields if f.name == "name")
    assert name_field.element is not None
    assert len(name_field.element.constraints) == 2
    assert any(isinstance(c, MinLength) for c in name_field.element.constraints)


def test_parse_attrs_with_list_fields() -> None:
    spec = parse(ListFieldAttrs)

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

    assert names.item is not None
    assert names.item.field_type is str
    assert names.collection_type is list
    assert len(names.item.constraints) == 2
    assert len(names.collection_constraints) == 2

    assert model_list.item is not None
    assert model_list.item.field_type is DefaultAttrs
    assert model_list.item.nested_model is not None
    assert model_list.collection_type is list

    assert unique_items.item is not None
    assert unique_items.item.field_type is str
    assert unique_items.collection_type is set
    assert unique_items.collection_constraints == (UniqueItems(True),)


def test_parse_attrs_with_dict_fields() -> None:
    spec = parse(DictFieldAttrs)

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

    assert models.collection_type is dict
    assert models.key is not None
    assert models.key.field_type is str
    assert models.value is not None
    assert models.value.field_type is DefaultAttrs
    assert models.value.nested_model is not None

    assert annotated_dicts.collection_type is dict
    assert annotated_dicts.collection_constraints == (MinItems(4),)
    assert annotated_dicts.key is not None
    assert annotated_dicts.key.constraints == (MinLength(5),)
    assert annotated_dicts.value is not None
    assert annotated_dicts.value.constraints == (MaxLength(10),)
