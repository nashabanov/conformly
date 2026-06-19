from dataclasses import dataclass
from typing import Annotated

from conformly import GreaterOrEqual, MinLength, case, cases
from conformly._internal.api.path import path


@dataclass
class Profile:
    age: Annotated[int, GreaterOrEqual(18)]


@dataclass
class User:
    name: Annotated[str, MinLength(5)]
    profile: Profile


def test_nested_valid_generation():
    data = case(User, valid=True)

    assert isinstance(data["profile"], dict)
    assert data["profile"]["age"] >= 18


def test_nested_invalid_first_strategy():
    data = case(User, valid=False, strategy="first")

    assert len(data["name"]) < 5


def test_nested_invalid_by_dotten_path():
    data = case(User, valid=False, strategy="profile.age")

    assert data["profile"]["age"] < 18


def test_nested_invalid_all_strategy():
    data = cases(User, valid=False, strategy="all")

    assert len(data) == 2

    violated = {"name" if len(d["name"]) < 5 else "profile.age" for d in data}

    assert violated == {"name", "profile.age"}


def test_nested_overrides() -> None:
    user = case(
        User, valid=True, overrides=[path(User, lambda u: u.profile.age).set(19)]
    )
    assert user["profile"]["age"] == 19
