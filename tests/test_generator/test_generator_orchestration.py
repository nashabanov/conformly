import pytest

from dataspec.generator.orchestration import (
    generate,
    generate_field,
    generate_invalid,
    generate_valid,
)
from dataspec.generator.registry import _generators, register
from dataspec.specs import ConstraintSpec, FieldSpec, ModelSpec


class TestStingGenerator:
    def supports(self, field: FieldSpec) -> bool:
        return field.type is str

    def generate_value(self, constraints: list[ConstraintSpec], valid: bool) -> str:
        from dataspec.generator.types.string import generate

        return generate(constraints, valid)


@pytest.fixture(autouse=True)
def fresh_registry():
    register(TestStingGenerator())
    yield
    _generators.clear()


simple_string_field = FieldSpec(
    name="name",
    type=str,
    constraints=[
        ConstraintSpec(
            constraint_type="max_length",
            value=40,
        )
    ],
)

default_string_field = FieldSpec(name="city", type=str, default="Palo Alto")

optional_string_field = FieldSpec(
    name="description", type=str, nullable=True, default="simple description"
)


simple_model = ModelSpec(
    name="User", type="dataclass", fields=[simple_string_field, default_string_field]
)


# ===== TESTS FOR generate_field() =====


def test_generate_field_valid_simple_string():
    field_value = generate_field(simple_string_field, valid=True)
    assert type(field_value) is str
    assert len(field_value) <= 40


def test_generate_field_invalid_simple_string():
    field_value = generate_field(simple_string_field, valid=False)
    assert type(field_value) is str
    assert len(field_value) > 40


def test_generate_field_valid_bool():
    assert (
        type(generate_field(FieldSpec(name="is_admin", type=bool), valid=True)) is bool
    )


def test_generate_field_invalid_bool():
    pass


def test_generate_field_valid_default():
    assert generate_field(default_string_field, valid=True) == "Palo Alto"


def test_generate_field_optional():
    assert generate_field(optional_string_field, valid=True) is None


@pytest.mark.parametrize(
    "field_type",
    [
        list,
        dict,
        float,
    ],
)
def test_generate_field_invalid_type(field_type):
    with pytest.raises(TypeError):
        generate_field(FieldSpec(name="unsupported", type=field_type), valid=True)


# ===== TEST FOR generate_invalid() =====


def test_generate_invalid_simpe_model():
    invalid_item = generate_invalid(simple_model, 0)
    assert type(invalid_item) is dict
    assert type(invalid_item["name"]) is str
    assert len(invalid_item["name"]) > 40
    assert type(invalid_item["city"]) is str
    assert invalid_item["city"] == "Palo Alto"


def test_generate_invalid_skipping_fields_without_constraint():
    invalid_item = generate_invalid(simple_model, 1)
    assert type(invalid_item) is dict
    assert type(invalid_item["name"]) is str
    assert len(invalid_item["name"]) <= 40
    assert type(invalid_item["city"]) is str
    assert invalid_item["city"] == "Palo Alto"


# ===== TEST FOR generate_valid() =====


def test_generate_valid_simple_model():
    valid_item = generate_valid(simple_model)
    assert type(valid_item) is dict
    assert type(valid_item["name"]) is str
    assert len(valid_item["name"]) <= 40
    assert type(valid_item["city"]) is str
    assert valid_item["city"] == "Palo Alto"


# ===== TEST FOR generate() =====


def test_generate_simple_model_valid():
    item = generate(simple_model, valid=True)
    assert type(item) is dict
    assert type(item["name"]) is str
    assert len(item["name"]) <= 40
    assert type(item["city"]) is str
    assert item["city"] == "Palo Alto"


def test_generate_simple_model_invalid_one_field_constraints():
    items = generate(simple_model, valid=False)
    assert type(items) is list
    invalid_item = items[0]
    assert len(items) == 1
    assert type(invalid_item) is dict
    assert type(invalid_item["name"]) is str
    assert len(invalid_item["name"]) > 40
    assert invalid_item["city"] == "Palo Alto"
