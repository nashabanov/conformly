from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Literal, Optional, Union

import pytest

from conformly.constraints import Constraint, Email, OneOf
from conformly.parsing.type_analysis import (
    extract_runtime_type_and_constraints,
    is_nullable,
)
from conformly.types import ENUMERATED_TYPE


@dataclass
class DummyDataclass:
    name: str
    age: int


class BaseEnum(Enum):
    a = "a"
    b = "b"


# ====== TESTS FOR extract_runtime_type_and_constraints() =====


def assert_constraints_equal(
    actual: tuple[Constraint, ...], expected: tuple[Constraint, ...]
) -> None:
    assert actual == expected, f"Expected {expected}, got {actual}"


def test_extract_runtime_type_plain():
    runtime_type, constraints = extract_runtime_type_and_constraints(int, "field")
    assert runtime_type is int
    assert constraints == ()

    runtime_type, constraints = extract_runtime_type_and_constraints(
        DummyDataclass, "field"
    )
    assert runtime_type is DummyDataclass
    assert constraints == ()


def test_extract_runtime_type_optional():
    runtime_type, constraints = extract_runtime_type_and_constraints(
        Optional[int],  # noqa: UP045
        "field",
    )
    assert runtime_type is int
    assert constraints == ()

    runtime_type, constraints = extract_runtime_type_and_constraints(
        Optional[DummyDataclass],  # noqa: UP045
        "field",
    )
    assert runtime_type is DummyDataclass
    assert constraints == ()


def test_extract_runtime_type_union_with_none():
    runtime_type, constraints = extract_runtime_type_and_constraints(
        DummyDataclass | None, "field"
    )
    assert runtime_type is DummyDataclass
    assert constraints == ()

    runtime_type, constraints = extract_runtime_type_and_constraints(
        Union[int, None],  # noqa: UP007
        "field",
    )
    assert runtime_type is int
    assert constraints == ()


def test_extract_runtime_type_annotated():
    annotated = Annotated[DummyDataclass, "metadata"]
    runtime_type, constraints = extract_runtime_type_and_constraints(annotated, "field")
    assert runtime_type is DummyDataclass
    assert constraints == ()


def test_extract_runtime_type_annotated_optional():
    annotated = Annotated[int | None, "metadata"]
    runtime_type, constraints = extract_runtime_type_and_constraints(annotated, "field")
    assert runtime_type is int
    assert constraints == ()


def test_extract_runtime_type_invalid_union():
    with pytest.raises(TypeError, match="unsupported union type"):
        extract_runtime_type_and_constraints(int | str, "field")

    with pytest.raises(TypeError, match="unsupported union type"):
        extract_runtime_type_and_constraints(int | DummyDataclass | None, "field")


def test_extract_runtime_type_literal():
    runtime_type, constraints = extract_runtime_type_and_constraints(
        Literal[1, 2], "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf((1, 2)),))


def test_extract_runtime_type_optional_literal():
    runtime_type, constraints = extract_runtime_type_and_constraints(
        Optional[Literal[1, 2]],  # noqa: UP045
        "field",
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf((1, 2)),))


def test_extract_runtime_type_literal_union_with_none():
    runtime_type, constraints = extract_runtime_type_and_constraints(
        Literal["a", "b"] | None, "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf(("a", "b")),))


def test_extract_runtime_type_heterogeneous_literal():
    runtime_type, constraints = extract_runtime_type_and_constraints(
        Literal[1, "a", 2.0, True], "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf((1, "a", 2.0, True)),))


def test_extract_runtime_type_enum():
    runtime_type, constraints = extract_runtime_type_and_constraints(BaseEnum, "field")
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf(("a", "b")),))


def test_extract_runtime_type_optional_enum():
    runtime_type, constraints = extract_runtime_type_and_constraints(
        Optional[BaseEnum],  # noqa: UP045
        "field",
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf(("a", "b")),))


def test_extract_runtime_type_empty_enum():
    class EmptyEnum(Enum):
        pass

    with pytest.raises(TypeError, match="empty Enum"):
        extract_runtime_type_and_constraints(EmptyEnum, "field")


class HeterogeneousEnum(Enum):
    INT = 1
    STR = "text"
    FLOAT = 3.14


def test_extract_runtime_type_heterogeneous_enum():
    runtime_type, constraints = extract_runtime_type_and_constraints(
        HeterogeneousEnum, "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf((1, "text", 3.14)),))


def test_extract_runtime_type_only_none():
    with pytest.raises(TypeError, match="unsupported type annotation"):
        extract_runtime_type_and_constraints(None, "field")


def test_extract_runtime_type_unsupported_annotation():
    with pytest.raises(TypeError, match="unsupported type annotation"):
        extract_runtime_type_and_constraints(list[int], "field")


def test_extract_runtime_type_email():
    assert extract_runtime_type_and_constraints(Email, "email") == (Email, ())


# ====== TESTS FOR is_nullable() ======


def test_is_nullable_optional_str():
    assert is_nullable(str | None)


def test_is_nullable_optional_int():
    assert is_nullable(int | None)


def test_is_nullable_union_with_none():
    assert is_nullable(str | None)


def test_is_nullable_union_multiple_with_none():
    assert is_nullable(str | int | None)


def test_is_nullable_not_optional_str():
    assert not is_nullable(str)


def test_is_nullable_not_optional_int():
    assert not is_nullable(int)


def test_is_nullable_union_without_none():
    assert not is_nullable(str | int)


def test_is_nullable_list():
    assert not is_nullable(list)


def test_is_nullable_annotated_union():
    assert is_nullable(Annotated[int | None, "ge=0"])


def test_is_nullable_annotated_not_optional():
    assert not is_nullable(Annotated[int, "ge=0"])
