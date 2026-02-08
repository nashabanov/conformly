from dataclasses import dataclass
from typing import Annotated, Any

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from pydantic.types import StringConstraints
from pydantic_core import PydanticUndefined
import pytest

from conformly.constraints import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    Pattern,
)
from conformly.parsing.adapters.pydantic import (
    _parse_default,
    _parse_fieldinfo_constraints,
    supports,
)
from conformly.types import _UNSET


class SimpleModel(BaseModel):
    name: str
    age: int
    email: str
    is_active: bool = True


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
    result = _parse_default(field_info, field_name, PydanticUndefined)
    assert result == expected


def test_parse_default_raises_default_factory() -> None:
    class Model(BaseModel):
        list_factory: list[str] = Field(default_factory=list)

    field_info = _get_field_info(Model, "list_factory")

    with pytest.raises(NotImplementedError):
        _parse_default(field_info, "list_factory", NotImplementedError)
