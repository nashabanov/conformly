from dataclasses import dataclass

import pytest

from conformly import V
from conformly._internal.api.path import PathSelector, parse_strategy_input, path
from conformly.exceptions import GenerationError


@dataclass
class Profile:
    email: str
    bio: str


@dataclass
class User:
    username: str
    age: int
    profile: Profile


def test_path_string_mode_simple():
    selector = path("username")
    assert isinstance(selector, PathSelector)
    assert selector.raw_path == "username"
    assert selector.forced_violation is None


def test_path_string_mode_nested():
    selector = path("profile.email")
    assert selector.raw_path == "profile.email"


def test_path_string_mode_with_violate():
    selector = path("age").violate(V.BELOW_MIN)
    assert selector.raw_path == "age"
    assert selector.forced_violation == V.BELOW_MIN


def test_path_string_mode_rejects_lambda():
    with pytest.raises(GenerationError):
        path("username", lambda u: u.username)  # type: ignore


def test_path_lambda_simple():
    selector = path(User, lambda u: u.username)
    assert selector.raw_path == "username"


def test_path_lambda_nested():
    selector = path(User, lambda u: u.profile.email)
    assert selector.raw_path == "profile.email"


def test_path_lambda_with_violate():
    selector = path(User, lambda u: u.profile.bio).violate(V.TOO_LONG)
    assert selector.raw_path == "profile.bio"
    assert selector.forced_violation == V.TOO_LONG


def test_path_lambda_rejects_no_expr():
    with pytest.raises(GenerationError):
        path(User)  # type: ignore


def test_path_lambda_rejects_no_args():
    with pytest.raises(GenerationError):
        path(User, lambda: User)  # type: ignore


def test_path_lambda_rejects_subscript():
    with pytest.raises(GenerationError):
        path(User, lambda u: u.profile[0])  # type: ignore


def test_path_lambda_rejects_method_call():
    with pytest.raises(GenerationError):
        path(User, lambda u: u.profile.get("email"))  # type: ignore


def test_path_lambda_rejects_wrong_variable():
    other_var = User(username="x", age=1, profile=Profile(email="y", bio="z"))
    with pytest.raises(GenerationError):
        path(User, lambda u: other_var.profile)


def test_path_lambda_rejects_literal():
    with pytest.raises(GenerationError):
        path(User, lambda u: "just_a_string")


def test_parse_strategy_string_simple():
    raw, violation = parse_strategy_input("username")
    assert raw == "username"
    assert violation is None


def test_parse_strategy_string_with_violation():
    raw, violation = parse_strategy_input("age::below_min")
    assert raw == "age"
    assert violation == V.BELOW_MIN


def test_parse_strategy_string_invalid_violation():
    with pytest.raises(GenerationError, match="invalid_violation_type"):
        parse_strategy_input("age::non_existent_violation")


def test_parse_strategy_path_selector():
    selector = path(User, lambda u: u.profile.email).violate(V.TOO_SHORT)
    raw, violation = parse_strategy_input(selector)
    assert raw == "profile.email"
    assert violation == V.TOO_SHORT


def test_parse_strategy_path_selector_no_violation():
    selector = path("username")
    raw, violation = parse_strategy_input(selector)
    assert raw == "username"
    assert violation is None
