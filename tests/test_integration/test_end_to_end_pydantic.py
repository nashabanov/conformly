import pytest

pytest.importorskip("pydantic", reason="Pydantic adapter requires 'pydantic' package")

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from conformly import case


def test_registry_routes_pydantic_model_to_adapter() -> None:
    class User(BaseModel):
        name: str = Field(min_length=2, max_length=50)
        age: int = Field(ge=0, le=150)
        role: Literal["user", "admin"]
        rating: int = Field(ge=0, le=100, multiple_of=5)

    result = case(User, valid=True)
    assert 2 <= len(result["name"]) <= 50
    assert 0 <= result["age"] <= 150
    assert result["role"] in ("user", "admin")
    assert 0 <= result["rating"] <= 100 and result["rating"] % 5 == 0


def test_default_factory() -> None:
    def factory() -> int:
        return 42

    class Model(BaseModel):
        value: int = Field(default_factory=factory)

    result = case(Model, valid=True)

    assert result["value"] == 42


def test_default_factory_called_each_time() -> None:
    counter = 0

    def factory() -> int:
        nonlocal counter
        counter += 1
        return counter

    class Model(BaseModel):
        value: int = Field(default_factory=factory)

    result1 = case(Model, valid=True)
    result2 = case(Model, valid=True)

    assert result1["value"] == 1
    assert result2["value"] == 2


class EmailModel(BaseModel):
    email: EmailStr


@pytest.mark.xfail
def test_emailstr_valid() -> None:
    result = case(EmailModel, valid=True)

    assert "email" in result
    assert isinstance(result["email"], str)

    try:
        from email_validator import validate_email

        validate_email(result["email"], check_deliverability=False)

    except ImportError:
        pass


def test_emailstr_invalid() -> None:
    result = case(EmailModel, valid=False)

    assert "email" in result
    assert isinstance(result["email"], str)

    try:
        from email_validator import EmailSyntaxError, validate_email

        with pytest.raises(EmailSyntaxError):
            validate_email(result["email"], check_deliverability=False)

    except ImportError:
        pass
