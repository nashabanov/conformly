import uuid

from _models import User, UserUUID
import pytest

from conformly import (
    case,
    cases,
    path,
)


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
        result = case(UserUUID, valid=False, strategy="id::wrong_uuid_character")
        hex_clean = result["id"].replace("-", "").lower()
        assert not all(c in "0123456789abcdef" for c in hex_clean)


class TestDeterministicGeneration:
    def test_same_seed_same_output(self) -> None:
        user1 = case(User, seed=42)
        user2 = case(User, seed=42)
        assert user1 == user2

    def test_different_seed_different_output(self) -> None:
        user1 = case(User, seed=44)
        user2 = case(User, seed=125)
        assert user1 != user2

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
