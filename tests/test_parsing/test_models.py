import pytest

from conformly._internal.parsing import FieldSpec, ModelSpec
from conformly.constraints import Constraint, GreaterOrEqual, MaxLength, MinLength


@pytest.fixture
def default_constraint_min() -> Constraint:
    return MinLength(10)


@pytest.fixture
def default_constraint_max() -> Constraint:
    return MaxLength(100)


@pytest.fixture
def default_field() -> FieldSpec:
    return FieldSpec(
        name="name",
        field_type=str,
        constraints=(MaxLength(30),),
    )


@pytest.fixture
def optional_field() -> FieldSpec:
    return FieldSpec(
        name="age",
        field_type=int,
        constraints=(GreaterOrEqual(18),),
        nullable=True,
        default=20,
    )


def test_field_spec_creation(
    default_constraint_min: Constraint, default_constraint_max: Constraint
) -> None:
    field = FieldSpec(
        name="age",
        field_type=int,
        constraints=(default_constraint_min, default_constraint_max),
    )
    assert field.name == "age"
    assert field.field_type is int
    assert len(field.constraints) == 2


def test_field_spec_repr(default_constraint_min: Constraint) -> None:
    field = FieldSpec(
        name="count", field_type=int, constraints=(default_constraint_min,)
    )
    repr_str = repr(field)
    assert "count" in repr_str
    assert "int" in repr_str
    assert "MinLength(value=10)" in repr_str


def test_field_spec_has_default(default_constraint_min: Constraint) -> None:
    field = FieldSpec(
        name="count", field_type=int, constraints=(default_constraint_min,), default=10
    )
    assert field.has_default()


def test_field_spec_has_no_default(default_constraint_min: Constraint) -> None:
    field = FieldSpec(
        name="count", field_type=int, constraints=(default_constraint_min,)
    )
    assert not field.has_default()


def test_field_spec_nullable_field_not_optional(
    default_constraint_min: Constraint,
) -> None:
    field = FieldSpec(
        name="count",
        field_type=int,
        constraints=(default_constraint_min,),
        nullable=True,
    )
    assert field.is_optional()


def test_field_spec_nullable_field_optional(default_constraint_min: Constraint) -> None:
    field = FieldSpec(
        name="count",
        field_type=int,
        constraints=(default_constraint_min,),
        default=100,
        nullable=False,
    )
    assert not field.is_optional()


def test_field_spec_not_optional_not_nullable(
    default_constraint_min: Constraint,
) -> None:
    field = FieldSpec(
        name="count",
        field_type=int,
        constraints=(default_constraint_min,),
    )
    assert not field.has_default()


def test_create_model_spec(default_field: FieldSpec) -> None:
    model = ModelSpec(name="User", type="dataclass", fields=(default_field,))
    assert model.name == "User"
    assert model.type == "dataclass"
    assert len(model.fields) == 1


def test_get_field(default_field: FieldSpec, optional_field: FieldSpec) -> None:
    model = ModelSpec(
        name="User", type="dataclass", fields=(default_field, optional_field)
    )
    field1 = model.get_field(default_field.name)
    field2 = model.get_field(optional_field.name)
    assert field1.name == default_field.name
    assert field2.name == optional_field.name


def test_get_spec_raises_on_missing(default_field: FieldSpec) -> None:
    model = ModelSpec(name="User", type="dataclass", fields=(default_field,))
    with pytest.raises(KeyError, match=r"Field 'age' is not defined in model: 'User'"):
        model.get_field("age")


def test_get_filtred_fields(
    default_field: FieldSpec, optional_field: FieldSpec
) -> None:
    model = ModelSpec(
        name="User", type="dataclass", fields=(default_field, optional_field)
    )
    required_fields = model.get_requiered_fields()
    optional_fields = model.get_optional_fields()
    assert len(required_fields) == 1
    assert required_fields[0].name == default_field.name
    assert len(optional_fields) == 1
    assert optional_fields[0].name == optional_field.name


def test_model_repr() -> None:
    field1 = FieldSpec(name="id", field_type=int)
    field2 = FieldSpec(name="name", field_type=str, nullable=True)
    model = ModelSpec(name="User", type="dataclass", fields=(field1, field2))

    repr_str = repr(model)

    expected = (
        f"Model(name='User', type='dataclass', fields={[repr(field1), repr(field2)]!r})"
    )
    assert repr_str == expected
