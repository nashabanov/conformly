import pytest

from dataspec.models.field_spec import ConstraintSpec, FieldSpec


@pytest.fixture
def default_constraint_min():
    return ConstraintSpec("min", 10)


@pytest.fixture
def default_constraint_max():
    return ConstraintSpec("max", 100)


def test_constraint_spec_repr(default_constraint_min):
    assert repr(default_constraint_min) == "Constraint(min=10)"


def test_field_spec_creation(default_constraint_min, default_constraint_max):
    field = FieldSpec(
        name="age",
        type=int,
        constraints=[default_constraint_min, default_constraint_max],
    )
    assert field.name == "age"
    assert field.type is int
    assert len(field.constraints) == 2


def test_constraint_found(default_constraint_min):
    field = FieldSpec(name="age", type=int, constraints=[default_constraint_min])
    assert isinstance(field.get_constraint("min"), ConstraintSpec)


def test_get_constraint_raises_on_missing(default_constraint_min):
    field = FieldSpec(name="age", type=int, constraints=[default_constraint_min])
    with pytest.raises(
        KeyError, match=r"Constraint 'max' is not defined for field: 'age'"
    ):
        field.get_constraint("max")


def test_field_spec_repr(default_constraint_min):
    field = FieldSpec(name="count", type=int, constraints=[default_constraint_min])
    repr_str = repr(field)
    assert "count" in repr_str
    assert "int" in repr_str
    assert "Constraint(min=10)" in repr_str


def test_field_spec_has_default(default_constraint_min):
    field = FieldSpec(
        name="count", type=int, constraints=[default_constraint_min], default=10
    )
    assert field.has_default()


def test_field_spec_has_no_default(default_constraint_min):
    field = FieldSpec(name="count", type=int, constraints=[default_constraint_min])
    assert not field.has_default()


def test_field_spec_nullable_field_not_optional(default_constraint_min):
    field = FieldSpec(
        name="count",
        type=int,
        constraints=[default_constraint_min],
        nullable=True,
    )
    assert field.is_optional()


def test_field_spec_nullable_field_optional(default_constraint_min):
    field = FieldSpec(
        name="count",
        type=int,
        constraints=[default_constraint_min],
        default=100,
        nullable=False,
    )
    assert field.is_optional()


def test_field_spec_not_optional_not_nullable(default_constraint_min):
    field = FieldSpec(
        name="count",
        type=int,
        constraints=[default_constraint_min],
    )
    assert not field.has_default()


def test_field_spec_default_constraints():
    field = FieldSpec(name="x", type=int)
    assert field.constraints == []
    with pytest.raises(
        KeyError, match=r"Constraint 'min' is not defined for field: 'x'"
    ):
        field.get_constraint("min")
