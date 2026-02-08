import pytest

pytest.importorskip("pydantic", reason="Pydantic adapter requires 'pydantic' package")

from typing import Literal

from pydantic import BaseModel, Field

from conformly import case


def test_registry_routes_pydantic_model_to_adapter() -> None:
    """Smoke-test: Pydantic model → registry → adapter → valid ModelSpec"""

    class User(BaseModel):
        name: str = Field(min_length=2, max_length=50)
        age: int = Field(ge=0, le=150)
        role: Literal["user", "admin"]

    result = case(User, valid=True)
    assert 2 <= len(result["name"]) <= 50
    assert 0 <= result["age"] <= 150
    assert result["role"] in ("user", "admin")
