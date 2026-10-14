from dataclasses import FrozenInstanceError, dataclass

import pytest

from conformly import V, path
from conformly._internal.api.path import PathSelector
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


@pytest.mark.parametrize("value", [None, "Alice", 0, False])
def test_path_tracks_explicit_override_without_mutating_selector(value):
    selector = path("username")
    overridden = selector.set(value)

    assert selector.override is None
    assert not selector.has_override
    assert overridden.override == value
    assert overridden.has_override
    assert overridden.forced_violation is None
    assert overridden != selector
    with pytest.raises(FrozenInstanceError):
        overridden.has_override = False


def test_path_methods_replace_configuration():
    overridden = path("username").violate(V.TOO_SHORT).set(None)
    assert overridden.has_override
    assert overridden.override is None
    assert overridden.forced_violation is None

    violated = overridden.violate(V.TOO_SHORT)
    assert not violated.has_override
    assert violated.override is None
    assert violated.forced_violation == V.TOO_SHORT
    assert overridden.has_override
