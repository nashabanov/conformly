from collections.abc import Sequence

import pytest

from conformly.constraints import Constraint, MaxLength
from conformly.generator.orchestration import (
    generate_field,
    generate_invalid,
    generate_valid,
)
from conformly.generator.registry import _generators, register
from conformly.specs import FieldSpec, ModelSpec


class TestStringGenerator:
    def supports(self, field: FieldSpec) -> bool:
        return field.type is str

    def generate_value(self, constraints: Sequence[Constraint], valid: bool) -> str:
        from conformly.generator.types.string import generate_value

        return generate_value(constraints, valid)


@pytest.fixture(autouse=True)
def fresh_registry():
    original = list(_generators)
    register(TestStringGenerator())
    yield
    _generators.clear()
    for gen in original:
        _generators.append(gen)


# --- Поля ---

simple_string_field = FieldSpec(
    name="name",
    type=str,
    constraints=[MaxLength(40)],
)

default_string_field = FieldSpec(name="city", type=str, default="Palo Alto")

optional_string_field = FieldSpec(
    name="description", type=str, nullable=True, default="simple description"
)

bool_field = FieldSpec(name="is_admin", type=bool)

simple_model = ModelSpec(
    name="User", type="dataclass", fields=[simple_string_field, default_string_field]
)


address_spec = ModelSpec(
    name="Address",
    type="dataclass",
    fields=[
        FieldSpec(name="city", type=str, constraints=[MaxLength(30)]),
        FieldSpec(name="zip", type=str, constraints=[MaxLength(20)]),
    ],
)

profile_spec = ModelSpec(
    name="Profile",
    type="dataclass",
    fields=[
        FieldSpec(
            name="email",
            type=str,
            constraints=[MaxLength(30)],
        ),
        FieldSpec(
            name="address",
            type=object,
            nested_model=address_spec,
        ),
    ],
)

model_with_nested = ModelSpec(
    name="User",
    type="dataclass",
    fields=[
        FieldSpec(
            name="username",
            type=str,
            constraints=[MaxLength(20)],
        ),
        FieldSpec(
            name="profile",
            type=object,
            nested_model=profile_spec,
        ),
    ],
)


# ===== TESTS FOR generate_field() =====


def test_generate_field_valid_simple_string():
    field_value = generate_field(simple_string_field, valid=True)
    assert isinstance(field_value, str)
    assert len(field_value) <= 40


def test_generate_field_invalid_simple_string():
    field_value = generate_field(simple_string_field, valid=False)
    assert isinstance(field_value, str)
    assert len(field_value) > 40


def test_generate_field_valid_bool():
    value = generate_field(bool_field, valid=True)
    assert isinstance(value, bool)


def test_generate_field_valid_default():
    assert generate_field(default_string_field, valid=True) == "Palo Alto"


def test_generate_field_optional():
    # Поведение: если поле optional (nullable=True), возвращаем None даже при valid=True
    assert generate_field(optional_string_field, valid=True) is None


@pytest.mark.parametrize("field_type", [list, dict])
def test_generate_field_unsupported_type(field_type):
    with pytest.raises(TypeError, match="No generators found"):
        generate_field(FieldSpec(name="unsupported", type=field_type), valid=True)


# ===== TEST FOR generate_invalid() =====


def test_generate_invalid_simple_model():
    invalid_item = generate_invalid(simple_model, (0,))  # нарушаем поле 0 ("name")
    assert isinstance(invalid_item, dict)
    assert isinstance(invalid_item["name"], str)
    assert len(invalid_item["name"]) > 40
    assert invalid_item["city"] == "Palo Alto"


def test_generate_invalid_skipping_fields_without_constraint():
    with pytest.raises(ValueError):
        generate_invalid(simple_model, (1,))


def test_generate_invalid_nested_top_level():
    invalid_item = generate_invalid(model_with_nested, (0,))
    assert len(invalid_item["username"]) > 20


def test_generate_invalid_nested():
    invalid_item = generate_invalid(model_with_nested, (1, 0))
    assert len(invalid_item["profile"]["email"]) > 30


def test_generate_invalid_deep_nested():
    invalid_item = generate_invalid(model_with_nested, (1, 1, 1))
    assert len(invalid_item["profile"]["address"]["zip"]) > 20


# ===== TEST FOR generate_valid() =====


def test_generate_valid_simple_model():
    valid_item = generate_valid(simple_model)
    assert isinstance(valid_item, dict)
    assert isinstance(valid_item["name"], str)
    assert len(valid_item["name"]) <= 40
    assert valid_item["city"] == "Palo Alto"


def test_generate_valid_nested_model():
    valid_item = generate_valid(model_with_nested)
    assert isinstance(valid_item, dict)
    assert isinstance(valid_item["profile"], dict)
    assert isinstance(valid_item["profile"]["address"], dict)
    assert isinstance(valid_item["profile"]["address"]["city"], str)
    assert len(valid_item["profile"]["address"]["city"]) <= 30
    assert len(valid_item["username"]) <= 20
