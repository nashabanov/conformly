import pytest

pytest.importorskip("pydantic", reason="Pydantic adapter requires 'pydantic' package")

from dataclasses import dataclass
from enum import Enum
import re
from typing import Annotated, Any

from pydantic import BaseModel, EmailStr, Field
from pydantic.fields import FieldInfo
from pydantic.types import StringConstraints
from pydantic_core import PydanticUndefined

from conformly.constraints import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    OneOf,
    Pattern,
)
from conformly.fields import Email
from conformly.parsing.adapters.pydantic import (
    _parse_default,
    _parse_fieldinfo_constraints,
    parse,
    parse_field,
    parse_fields,
    supports,
)
from conformly.specs import ModelSpec
from conformly.types import _UNSET, ENUMERATED_TYPE


class SimpleModel(BaseModel):
    name: str
    age: int
    email: str
    is_active: bool = True


class Colors(Enum):
    red = "red"
    green = "green"


class ConstrainedModel(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    bio: str = Field(default="", max_length=280)
    tag: Annotated[
        str, StringConstraints(min_length=2, max_length=10, pattern=r"^[A-Z]+$")
    ]
    age: int = Field(ge=0, le=150)
    height: float = Field(gt=0.0, lt=3.0)
    status: str | None = Field(default=None, min_length=2)
    annotated_mixed: Annotated[
        int,
        Field(ge=1),
        Field(le=100),
    ]
    annotated_conformly_types: Annotated[int, GreaterThan(1)]
    color: Colors


def _get_field_info(model: type[BaseModel], name: str) -> FieldInfo:
    field_info = model.model_fields.get(name)
    assert field_info is not None
    return field_info


# ===== TESTS for supports() =====


def test_supports_valid() -> None:
    assert supports(SimpleModel)


def test_supports_invalid() -> None:
    @dataclass
    class SimpleDataclass:
        name: str

    assert not supports(SimpleDataclass)


# ===== TESTS for _parse_fieldinfo_constraints() =====


def test_parse_fieldinfo_constraints_string_field() -> None:
    field_info = _get_field_info(ConstrainedModel, "username")

    constraints = _parse_fieldinfo_constraints(field_info)
    assert len(constraints) == 3
    assert any(c == MinLength(3) for c in constraints)
    assert any(c == MaxLength(20) for c in constraints)
    assert any(c == Pattern(r"^[a-zA-Z0-9_]+$") for c in constraints)


def test_parse_fieldinfo_constraints_integer_field() -> None:
    field_info = _get_field_info(ConstrainedModel, "age")

    constraints = _parse_fieldinfo_constraints(field_info)
    assert len(constraints) == 2
    assert any(c == GreaterOrEqual(0) for c in constraints)
    assert any(c == LessOrEqual(150) for c in constraints)


def test_parse_fieldinfo_constraints_float_field() -> None:
    field_info = _get_field_info(ConstrainedModel, "height")

    constraints = _parse_fieldinfo_constraints(field_info)
    assert len(constraints) == 2
    assert any(c == GreaterThan(0.0) for c in constraints)
    assert any(c == LessThan(3.0) for c in constraints)


def test_parse_fieldinfo_constraints_annotated_string_constraints() -> None:
    field_info = _get_field_info(ConstrainedModel, "tag")

    constraints = _parse_fieldinfo_constraints(field_info)
    assert len(constraints) == 3
    assert any(c == MinLength(2) for c in constraints)
    assert any(c == MaxLength(10) for c in constraints)
    assert any(c == Pattern(r"^[A-Z]+$") for c in constraints)


def test_parse_fieldinfo_constraints_no_constraints() -> None:
    field_info = _get_field_info(SimpleModel, "name")
    assert _parse_fieldinfo_constraints(field_info) == ()


def test_parse_fieldinfo_constraints_annotated_multitiple_field() -> None:
    field_info = _get_field_info(ConstrainedModel, "annotated_mixed")

    constraints = _parse_fieldinfo_constraints(field_info)
    assert len(constraints) == 2
    assert any(c == GreaterOrEqual(1) for c in constraints)
    assert any(c == LessOrEqual(100) for c in constraints)


def test_parse_fieldinfo_constraints_annotated_conformly() -> None:
    field_info = _get_field_info(ConstrainedModel, "annotated_conformly_types")

    constraints = _parse_fieldinfo_constraints(field_info)
    assert len(constraints) == 1
    assert any(c == GreaterThan(1) for c in constraints)


def test_mixed_sources_preserve_all_constraints() -> None:
    class Model(BaseModel):
        value: Annotated[str, MinLength(5)] = Field(max_length=10)

    field_info = _get_field_info(Model, "value")
    constraints = _parse_fieldinfo_constraints(field_info)

    assert len(constraints) == 2
    assert any(c == MinLength(5) for c in constraints)
    assert any(c == MaxLength(10) for c in constraints)


# ===== TESTS for _parse_default() =====


@pytest.mark.parametrize(
    "field_name, expected",
    [
        ("str_default", "test"),
        ("none_default", None),
        ("int_default", 42),
        ("required_str", _UNSET),
    ],
)
def test_parse_default_valid(field_name: str, expected: Any) -> None:
    class Model(BaseModel):
        str_default: str = "test"
        none_default: str | None = None
        int_default: int = 42
        required_str: str

    field_info = _get_field_info(Model, field_name)
    result = _parse_default(field_info, PydanticUndefined)
    assert result == expected


def test_parse_default_raises_default_factory() -> None:
    class Model(BaseModel):
        list_factory: list[str] = Field(default_factory=list)

    field_info = _get_field_info(Model, "list_factory")

    assert callable(_parse_default(field_info, PydanticUndefined))


# ===== TESTS for parse_field() =====


def test_parse_field_basic() -> None:
    field_info = _get_field_info(ConstrainedModel, "bio")

    field_spec = parse_field(field_info, str, "bio", PydanticUndefined)
    assert field_spec.name == "bio"
    assert field_spec.has_constraints
    assert field_spec.has_default
    assert field_spec.default == ""
    assert not field_spec.nullable
    assert field_spec.type is str
    assert len(field_spec.constraints) == 1


def test_parse_field_enum() -> None:
    field_info = _get_field_info(ConstrainedModel, "color")

    field_spec = parse_field(field_info, Colors, "color", PydanticUndefined)
    assert field_spec.name == "color"
    assert field_spec.type == ENUMERATED_TYPE
    assert len(field_spec.constraints) == 1
    assert field_spec.constraints == (OneOf(("red", "green")),)


def test_parse_field_non_consistent_constraints() -> None:
    class Model(BaseModel):
        color: Annotated[Colors, MinLength(8)]

    field_info = _get_field_info(Model, "color")
    with pytest.raises(TypeError):
        parse_field(field_info, Colors, "color", PydanticUndefined)


def test_parse_field_nested_model() -> None:
    class Model(BaseModel):
        nested: SimpleModel

    field_info = _get_field_info(Model, "nested")

    field_spec = parse_field(field_info, SimpleModel, "nested", PydanticUndefined)
    assert field_spec.name == "nested"
    assert field_spec.type is SimpleModel
    assert isinstance(field_spec.nested_model, ModelSpec)


def test_parse_field_compiled_pattern() -> None:
    class Model(BaseModel):
        code: str = Field(pattern=re.compile(r"^[A-Z]{3}$"))

    constraints = _parse_fieldinfo_constraints(_get_field_info(Model, "code"))
    assert any(isinstance(c, Pattern) and c.regex == r"^[A-Z]{3}$" for c in constraints)


def test_parse_field_emailstr() -> None:
    class Model(BaseModel):
        email: EmailStr

    field_info = _get_field_info(Model, "email")
    field_spec = parse_field(
        field_info, field_info.annotation, "email", PydanticUndefined
    )
    assert field_spec.type is Email
    assert field_spec.constraints == ()


# ===== TESTS for parse_fields() =====


def test_parse_fields_count() -> None:
    assert len(parse_fields(SimpleModel, PydanticUndefined)) == 4


def test_parse_fields_types() -> None:
    fields = parse_fields(ConstrainedModel, PydanticUndefined)

    assert fields[0].type is str
    assert fields[6].type is int
    assert fields[8].type is ENUMERATED_TYPE
    assert fields[5].type is str


# ===== TESTS for parse() =====


def test_parse_non_pydantic() -> None:
    @dataclass
    class SimpleDataclass:
        name: str

    with pytest.raises(TypeError):
        parse(SimpleDataclass)


def test_parse_basic() -> None:
    model_spec = parse(SimpleModel)

    assert model_spec.name == "SimpleModel"
    assert model_spec.type == "pydantic"
    assert len(model_spec.fields) == 4


def test_parse_inherited_fields() -> None:
    class Base(BaseModel):
        id: int
        created_at: str

    class Derived(Base):
        name: str

    spec = parse(Derived)
    assert len(spec.fields) == 3
    assert {f.name for f in spec.fields} == {"id", "created_at", "name"}


def test_parse_empty_model() -> None:
    class Empty(BaseModel):
        pass

    spec = parse(Empty)
    assert len(spec.fields) == 0


def test_parse_emailstr() -> None:
    class Model(BaseModel):
        email: EmailStr

    spec = parse(Model)
    assert len(spec.fields) == 1
    field_spec = spec.fields[0]
    assert field_spec.type is Email
