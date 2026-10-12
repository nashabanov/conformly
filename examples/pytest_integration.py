"""Run directly or with pytest. Install pytest to use its test runner."""

from dataclasses import dataclass
from typing import Annotated, Any

from conformly import GreaterOrEqual, MinLength, case, cases


@dataclass
class CreateUser:
    username: Annotated[str, MinLength(3)]
    age: Annotated[int, GreaterOrEqual(18)]


def accepts(payload: dict[str, Any]) -> bool:
    """A small application validator matching the declared schema."""
    return (
        isinstance(payload.get("username"), str)
        and len(payload["username"]) >= 3
        and type(payload.get("age")) is int
        and payload["age"] >= 18
    )


def test_accepts_valid_users() -> None:
    for payload in cases(CreateUser, count=10):
        assert accepts(payload)


def test_rejects_invalid_users() -> None:
    for payload in cases(CreateUser, valid=False, strategy="all_violations"):
        assert not accepts(payload)


def test_targeted_age_rejection() -> None:
    assert not accepts(case(CreateUser, valid=False, strategy="age::below_min"))


if __name__ == "__main__":
    test_accepts_valid_users()
    test_rejects_invalid_users()
    test_targeted_age_rejection()
    print("Positive and negative validation checks passed.")
