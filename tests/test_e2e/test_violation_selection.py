import re

from _models import TupleModel, User
import pytest

from conformly import (
    V,
    case,
    cases,
    path,
)
from conformly.exceptions import GenerationError, PlanningError


class TestViolationTypeSyntax:
    def test_specific_violation_too_short(self):
        invalid = case(User, valid=False, target=path("username").violate(V.TOO_SHORT))
        assert len(invalid["username"]) < 3
        assert len(invalid["email"]) > 0  # Other fields valid

    def test_specific_violation_too_long(self):
        invalid = case(User, valid=False, target=path("bio").violate(V.TOO_LONG))
        assert len(invalid["bio"]) > 500
        assert len(invalid["username"]) >= 3  # Other fields valid

    def test_specific_violation_pattern_mismatch(self):
        invalid = case(
            User, valid=False, target=path("email").violate(V.PATTERN_MISMATCH)
        )
        assert not re.match(
            r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", invalid["email"]
        )
        assert len(invalid["username"]) >= 3

    def test_specific_violation_not_allowed_value(self):
        invalid = case(
            User, valid=False, target=path("role").violate(V.NOT_ALLOWED_VALUE)
        )
        assert invalid["role"] not in ["admin", "guest", "user"]

    def test_specific_violation_type_mismatch(self):
        invalid = case(
            User,
            valid=False,
            target=path("is_blocked").violate(V.TYPE_MISMATCH),
            allow_type_mismatch=True,
        )
        assert not isinstance(invalid["is_blocked"], bool)
        assert len(invalid["username"]) >= 3

    def test_cases_with_specific_violation(self):
        invalid_users = cases(
            User, valid=False, target=path("username").violate(V.TOO_SHORT), count=1
        )
        assert len(invalid_users) == 1
        for user in invalid_users:
            assert len(user["username"]) < 3


def test_generates_fixed_and_variadic_tuples() -> None:
    result = case(TupleModel, valid=True, seed=1)

    assert isinstance(result["fixed"], tuple)
    assert len(result["fixed"]) == 2
    assert len(result["fixed"][0]) >= 2
    assert isinstance(result["fixed"][1], int)
    assert isinstance(result["variadic"], tuple)
    assert len(result["variadic"]) >= 2


def test_generates_invalid_tuple_element() -> None:
    result = case(
        TupleModel, valid=False, target=path("fixed").violate(V.TOO_SHORT), seed=1
    )

    assert len(result["fixed"]) == 2
    assert len(result["fixed"][0]) < 2


def test_invalid_violation_type_raises() -> None:
    with pytest.raises(GenerationError):
        case(User, valid=False, strategy="username::invalid_violation")


def test_incompatible_violation_type_raises() -> None:
    with pytest.raises(PlanningError):
        case(User, valid=False, target=path("username").violate(V.BELOW_MIN))


def test_incompatible_violation_on_enum() -> None:
    with pytest.raises(PlanningError):
        case(User, valid=False, target=path("role").violate(V.BELOW_MIN))


def test_violation_with_allow_type_mismatch() -> None:
    invalid = case(
        User,
        valid=False,
        target=path("is_blocked").violate(V.TYPE_MISMATCH),
        allow_type_mismatch=True,
    )
    assert not isinstance(invalid["is_blocked"], (bool,))


def test_deterministic_violation_selection() -> None:
    results = [
        case(User, valid=False, target=path("username").violate(V.TOO_SHORT), seed=seed)
        for seed in (0, 1, -1)
    ]

    assert all(len(result["username"]) < 3 for result in results)


def test_other_fields_remain_valid() -> None:
    invalid = case(User, valid=False, target=path("email").violate(V.PATTERN_MISMATCH))

    assert not re.match(
        r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", invalid["email"]
    )

    assert len(invalid["username"]) >= 3
    assert 2 <= len(invalid["full_name"]) <= 100
    assert invalid["role"] in ["admin", "guest", "user"]
    assert len(invalid["bio"]) <= 500
    assert isinstance(invalid["is_blocked"], bool)


def test_case_vs_cases_with_specific_violation() -> None:
    case_result = case(
        User, valid=False, target=path("role").violate(V.NOT_ALLOWED_VALUE)
    )
    cases_result = cases(
        User, valid=False, target=path("role").violate(V.NOT_ALLOWED_VALUE), count=1
    )

    assert case_result["role"] not in ["admin", "guest", "user"]
    assert cases_result[0]["role"] not in ["admin", "guest", "user"]


def test_valid_flag_rejects_target() -> None:
    with pytest.raises(GenerationError):
        case(User, valid=True, target=path("username").violate(V.TOO_SHORT))


def test_field_not_found_with_violation() -> None:
    with pytest.raises(PlanningError) as exc_info:
        case(User, valid=False, target=path("nonexistent").violate(V.BELOW_MIN))

    assert exc_info.value.context["code"] == "field_not_found"


def test_available_violations_in_error_message() -> None:
    with pytest.raises(PlanningError) as exc_info:
        case(User, valid=False, target=path("username").violate(V.BELOW_MIN))

    assert exc_info.value.context["code"] == "invalid_forced_violation"
    assert "too_short" in exc_info.value.context["allowed"]


def test_auto_enable_structural_for_missing_field() -> None:
    invalid = case(
        User,
        valid=False,
        target=path("bio").violate(V.MISSING_FIELD),
    )
    assert "bio" not in invalid


def test_all_violations_count_with_new_syntax() -> None:
    invalid_users = cases(
        User,
        valid=False,
        strategy="all_violations",
        allow_type_mismatch=True,
        allow_structural_violations=True,
    )
    assert len(invalid_users) >= 8


def test_reproducibility_with_specific_violation() -> None:
    invalid1 = case(
        User, valid=False, target=path("username").violate(V.TOO_SHORT), seed=0
    )
    invalid2 = case(
        User, valid=False, target=path("username").violate(V.TOO_SHORT), seed=0
    )

    assert invalid1 == invalid2
    assert len(invalid1["username"]) < 3


def test_path_selector_specific_violation() -> None:
    invalid = case(User, valid=False, target=path("username").violate(V.TOO_SHORT))
    assert len(invalid["username"]) < 3
    assert len(invalid["email"]) > 0


def test_path_selector_structural_violation() -> None:
    invalid = case(
        User,
        valid=False,
        target=path("bio").violate(V.MISSING_FIELD),
    )

    assert "bio" not in invalid


def test_path_selector_structural_requires_violation() -> None:
    with pytest.raises(GenerationError):
        cases(
            User,
            valid=False,
            target=path("bio"),
            allow_structural_violations=True,
        )


def test_path_selector_incompatible_violation() -> None:
    with pytest.raises(PlanningError):
        case(
            User,
            valid=False,
            target=path("username").violate(V.BELOW_MIN),
        )


def test_path_selector_field_not_found() -> None:
    with pytest.raises(PlanningError):
        case(
            User,
            valid=False,
            target=path("nonexistent").violate(V.TOO_SHORT),
        )


def test_typed_selector_equals_string_selector() -> None:
    invalid1 = case(
        User,
        valid=False,
        target=path(User, lambda u: u.username).violate(V.TOO_SHORT),
        seed=0,
    )

    invalid2 = case(
        User,
        valid=False,
        target=path("username").violate(V.TOO_SHORT),
        seed=0,
    )

    assert invalid1 == invalid2
    assert len(invalid1["username"]) < 3
