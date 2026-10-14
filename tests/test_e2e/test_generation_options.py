from dataclasses import make_dataclass, replace
from typing import Annotated
import uuid

from _models import User, UserUUID
import pytest

from conformly import (
    MinLength,
    V,
    case,
    cases,
    path,
)
from conformly.exceptions import GenerationError


class TestUUIDGeneration:
    def test_valid_uuid(self):
        result = case(UserUUID, valid=True)

        assert isinstance(result["id"], str)
        parsed = uuid.UUID(result["id"])
        assert parsed.version == 4, f"Expected v4 UUID, got version {parsed.version}"
        assert result["id"] == str(parsed)

    def test_invalid_uuid_fails_strict_parsing(self):
        result = case(UserUUID, valid=False, seed=0)
        with pytest.raises(ValueError):
            uuid.UUID(result["id"])

    def test_valid_false_respects_violation_type(self):
        result = case(
            UserUUID, valid=False, target=path("id").violate(V.WRONG_UUID_CHARACTER)
        )
        hex_clean = result["id"].replace("-", "").lower()
        assert not all(c in "0123456789abcdef" for c in hex_clean)


class TestDeterministicGeneration:
    def test_same_seed_same_output(self) -> None:
        user1 = case(User, seed=42)
        user2 = case(User, seed=42)
        assert user1 == user2

    def test_same_seed_same_list(self) -> None:
        users1 = cases(User, seed=42)
        users2 = cases(User, seed=42)
        assert users1 == users2

    def test_invalid_generation_seeding(self) -> None:
        user1 = case(User, valid=False, seed=42)
        user2 = case(User, valid=False, seed=42)
        assert user1 == user2


class TestOverrides:
    def test_case_overrides(self) -> None:
        user = case(
            User,
            valid=True,
            overrides=[
                path(User, lambda u: u.full_name).set("Amogus"),
                path(User, lambda u: u.email).set("amogus@example.com"),
            ],
        )
        assert user["full_name"] == "Amogus"
        assert user["email"] == "amogus@example.com"

    def test_cases_overrides(self) -> None:
        users = cases(
            User,
            valid=True,
            overrides=[
                path(User, lambda u: u.full_name).set("Amogus"),
                path(User, lambda u: u.email).set("amogus@example.com"),
            ],
            count=4,
        )

        for u in users:
            assert u["full_name"] == "Amogus"
            assert u["email"] == "amogus@example.com"

    def test_cases_overrides_respected_when_field_not_invalidated(self) -> None:
        users = cases(
            User,
            valid=False,
            overrides=[
                path(User, lambda u: u.full_name).set("Amogus"),
            ],
            strategy="all",
        )

        assert users

        seen_valid_override = False
        seen_broken_override = False

        for user in users:
            if user["full_name"] == "Amogus":
                seen_valid_override = True
            else:
                seen_broken_override = True

        assert seen_valid_override, (
            "Override should be applied when field is not invalidated"
        )

        assert seen_broken_override, (
            "Override should be ignored when field is invalidated"
        )


@pytest.fixture
def override_model():
    name = Annotated[str, MinLength(3)]
    profile = make_dataclass("OverrideProfile", [("name", name)])
    return make_dataclass("OverrideUser", [("username", name), ("profile", profile)])


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("valid", [True, False])
@pytest.mark.parametrize("requested", ["nonexistent", "profile.nonexistent"])
def test_unknown_override_path(override_model, api, valid, requested):
    with pytest.raises(GenerationError) as error:
        api(
            override_model,
            valid=valid,
            seed=42,
            overrides=[path(requested).set("value")],
        )
    assert error.value.context["code"] == "invalid_override_path"
    assert error.value.context["path"] == requested
    assert set(error.value.context["available"]) == {
        "username",
        "profile",
        "profile.name",
    }


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("valid", [True, False])
@pytest.mark.parametrize(
    "selector",
    [
        path("username"),
        path("username").violate(V.TOO_SHORT),
        path("username").set(None).violate(V.TOO_SHORT),
        "username",
        replace(path("username").set(None), forced_violation=V.TOO_SHORT),
    ],
)
def test_invalid_override_selector(override_model, api, valid, selector):
    with pytest.raises(GenerationError) as error:
        api(override_model, valid=valid, seed=42, overrides=[selector])
    assert error.value.context["code"] == "invalid_override_selector"


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("valid", [True, False])
def test_nested_override_is_trusted_and_seeded(override_model, api, valid):
    kwargs = {
        "valid": valid,
        "seed": 42,
        "overrides": [path(override_model, lambda m: m.profile.name).set("x")],
    }
    result = api(override_model, **kwargs)
    assert result == api(override_model, **kwargs)
    payload = result[0] if api is cases else result
    assert payload["profile"]["name"] == "x"
    assert len(payload["username"]) >= 3 if valid else len(payload["username"]) < 3


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("values", [("Alice", None), (None, "Alice")])
def test_duplicate_overrides_use_last_value(override_model, api, values):
    result = api(
        override_model,
        seed=42,
        overrides=[path("username").set(value) for value in values],
    )
    payload = result[0] if api is cases else result
    assert payload["username"] == values[-1]


@pytest.mark.parametrize("api", [case, cases])
def test_explicit_none_target_override_is_ignored(override_model, api):
    kwargs = {
        "valid": False,
        "seed": 42,
        "target": path("username").violate(V.TOO_SHORT),
    }
    unrelated = path("profile.name").set(None)
    result = api(
        override_model, overrides=[path("username").set(None), unrelated], **kwargs
    )
    assert result == api(override_model, overrides=[unrelated], **kwargs)
    payload = result[0] if api is cases else result
    assert len(payload["username"]) < 3
    assert payload["profile"]["name"] is None
