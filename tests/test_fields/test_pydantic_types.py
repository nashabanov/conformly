import pytest

pytest.importorskip("pydantic", reason="Pydantic adapter requires 'pydantic' package")

from pydantic import BaseModel, ValidationError

from conformly import case
from conformly._internal.fields import SPECIAL_STRINGS


def get_pydantic_type(name: str) -> type | None:
    try:
        import pydantic

        if hasattr(pydantic, name):
            return getattr(pydantic, name)

        import pydantic.networks as networks

        return getattr(networks, name, None)
    except ImportError:
        return None


@pytest.mark.parametrize("spec", SPECIAL_STRINGS)
def test_pydantic_type_exists(spec):
    pydantic_type = get_pydantic_type(spec.pydantic_name)

    assert pydantic_type is not None, f"Pydantic type {spec.pydantic_name!r} not found"


@pytest.mark.parametrize("spec", SPECIAL_STRINGS)
def test_pydantic_type_is_class(spec):
    pydantic_type = get_pydantic_type(spec.pydantic_name)

    if pydantic_type is None:
        pytest.skip(f"{spec.pydantic_name} not available")

    assert isinstance(pydantic_type, type)


@pytest.mark.parametrize("spec", SPECIAL_STRINGS)
def test_pydantic_adapter_valid_generation(spec):
    pydantic_type = get_pydantic_type(spec.pydantic_name)
    if pydantic_type is None:
        pytest.skip(f"{spec.pydantic_name} not available")

    class TestModel(BaseModel):
        field: pydantic_type  # type: ignore

    result = case(TestModel, valid=True)

    assert "field" in result
    assert result["field"] is not None

    instance = TestModel(**result)

    value = instance.field

    if spec.pydantic_name == "EmailStr":
        assert isinstance(value, str)
        assert "@" in value

    elif spec.pydantic_name == "IPvAnyAddress":
        from ipaddress import IPv4Address, IPv6Address

        assert isinstance(value, (IPv4Address, IPv6Address))

    else:
        assert isinstance(value, pydantic_type)  # type: ignore

    normalized = str(value)
    re_instance = TestModel(field=normalized)

    assert str(re_instance.field) == normalized


@pytest.mark.parametrize("spec", SPECIAL_STRINGS)
def test_pydantic_adapter_invalid_generation(spec):
    pydantic_type = get_pydantic_type(spec.pydantic_name)
    if pydantic_type is None:
        pytest.skip(f"{spec.pydantic_name} not available")

    class TestModel(BaseModel):
        field: pydantic_type  # type: ignore

    result = case(TestModel, valid=False)

    with pytest.raises(ValidationError):
        TestModel(**result)
