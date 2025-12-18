import pytest

from conformly.generator.orchestration import (
    generate_field,
    generate_invalid,
    generate_valid,
)
from conformly.generator.registry import _generators, register
from conformly.specs import ConstraintSpec, FieldSpec, ModelSpec


class TestStringGenerator:
    def supports(self, field: FieldSpec) -> bool:
        return field.type is str

    def generate_value(self, constraints: list[ConstraintSpec], valid: bool) -> str:
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
    constraints=[ConstraintSpec(constraint_type="max_length", value=40)],
)

default_string_field = FieldSpec(name="city", type=str, default="Palo Alto")

optional_string_field = FieldSpec(
    name="description", type=str, nullable=True, default="simple description"
)

bool_field = FieldSpec(name="is_admin", type=bool)

simple_model = ModelSpec(
    name="User", type="dataclass", fields=[simple_string_field, default_string_field]
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
    invalid_item = generate_invalid(simple_model, 0)  # нарушаем поле 0 ("name")
    assert isinstance(invalid_item, dict)
    assert isinstance(invalid_item["name"], str)
    assert len(invalid_item["name"]) > 40
    assert invalid_item["city"] == "Palo Alto"


def test_generate_invalid_skipping_fields_without_constraint():
    # Поле 1 ("city") не имеет constraints → должно остаться валидным
    invalid_item = generate_invalid(simple_model, 1)
    assert isinstance(invalid_item, dict)
    assert isinstance(invalid_item["name"], str)
    assert len(invalid_item["name"]) <= 40  # не нарушено
    assert invalid_item["city"] == "Palo Alto"


# ===== TEST FOR generate_valid() =====


def test_generate_valid_simple_model():
    valid_item = generate_valid(simple_model)
    assert isinstance(valid_item, dict)
    assert isinstance(valid_item["name"], str)
    assert len(valid_item["name"]) <= 40
    assert valid_item["city"] == "Palo Alto"
