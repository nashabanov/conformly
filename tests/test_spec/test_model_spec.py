import pytest

from dataspec.specs import ConstraintSpec, FieldSpec, ModelSpec


@pytest.fixture
def default_field():
    return FieldSpec(
        name="name",
        type=str,
        constraints=[ConstraintSpec(constraint_type="length", value=30)],
    )


@pytest.fixture
def optional_field():
    return FieldSpec(
        name="age",
        type=int,
        constraints=[ConstraintSpec(constraint_type="min", value=18)],
        nullable=True,
        default=20,
    )


def test_create_model_spec(default_field):
    model = ModelSpec(name="User", type="dataclass", fields=[default_field])
    assert model.name == "User"
    assert model.type == "dataclass"
    assert len(model.fields) == 1


def test_get_field(default_field, optional_field):
    model = ModelSpec(
        name="User", type="dataclass", fields=[default_field, optional_field]
    )
    field1 = model.get_field(default_field.name)
    field2 = model.get_field(optional_field.name)
    assert field1.name == default_field.name
    assert field2.name == optional_field.name


def test_get_spec_raises_on_missing(default_field):
    model = ModelSpec(name="User", type="dataclass", fields=[default_field])
    with pytest.raises(KeyError, match=r"Field 'age' is not defined in model: 'User'"):
        model.get_field("age")


def test_get_filtred_fields(default_field, optional_field):
    model = ModelSpec(
        name="User", type="dataclass", fields=[default_field, optional_field]
    )
    required_fields = model.get_requiered_fields()
    optional_fields = model.get_optional_fields()
    assert len(required_fields) == 1
    assert required_fields[0].name == default_field.name
    assert len(optional_fields) == 1
    assert optional_fields[0].name == optional_field.name


def test_model_repr():
    field1 = FieldSpec(name="id", type=int)
    field2 = FieldSpec(name="name", type=str, nullable=True)
    model = ModelSpec(name="User", type="dataclass", fields=[field1, field2])

    repr_str = repr(model)

    expected = (
        f"Model(name='User', type='dataclass', fields={[repr(field1), repr(field2)]!r})"
    )
    assert repr_str == expected
