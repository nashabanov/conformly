"""Requires pip install 'conformly[pydantic]' (Pydantic 2)."""

from pydantic import BaseModel, Field, ValidationError

from conformly import V, case, path


class CreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    age: int = Field(ge=18)


payload = case(CreateUser)
user = CreateUser.model_validate(payload)
assert user.age >= 18
invalid = case(CreateUser, valid=False, target=path("age").violate(V.BELOW_MIN))
try:
    CreateUser.model_validate(invalid)
except ValidationError as error:
    assert any(
        e["loc"] == ("age",) and e["type"] == "greater_than_equal"
        for e in error.errors()
    )
else:
    raise AssertionError("Expected age validation to fail")
print(payload)
