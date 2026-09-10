import pytest

from conformly import GreaterThan, MinLength
from conformly._internal.constraints import OneOf
from conformly._internal.parser import ElementSpec, FieldSpec, ModelSpec
from conformly._internal.types import ENUMERATED_TYPE


@pytest.fixture
def simple_model_spec() -> ModelSpec:
    return ModelSpec(
        name="User",
        type="dataclass",
        fields=(
            FieldSpec(
                name="id", element=ElementSpec(int, constraints=(GreaterThan(0),))
            ),
            FieldSpec(
                name="name", element=ElementSpec(str, constraints=(MinLength(1),))
            ),
            FieldSpec("active", element=ElementSpec(bool)),
            FieldSpec(
                name="type",
                element=ElementSpec(
                    ENUMERATED_TYPE, constraints=(OneOf(("user", "admin")),)
                ),
            ),
        ),
    )


@pytest.fixture
def nested_model_spec() -> ModelSpec:
    address = ModelSpec(
        name="Address",
        type="dataclass",
        fields=(FieldSpec(name="street", element=ElementSpec(str, ())),),
    )
    return ModelSpec(
        name="Person",
        type="dataclass",
        fields=(
            FieldSpec(name="name", element=ElementSpec(str, ())),
            FieldSpec("addr", element=ElementSpec(dict, (), nested_model=address)),
        ),
    )
