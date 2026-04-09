from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Literal, Optional, Union

import pytest

from conformly._internal.constraints import Constraint, MaxLength, MinLength, OneOf
from conformly._internal.fields import Email
from conformly._internal.parsing.extractors.types import (
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


def test_extract_runtime_type_plain() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(int, "field")
    assert runtime_type is int
    assert constraints == ()

    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        DummyDataclass, "field"
    )
    assert runtime_type is DummyDataclass
    assert constraints == ()


def test_extract_runtime_type_optional() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        Optional[int],  # noqa: UP045
        "field",
    )
    assert runtime_type is int
    assert constraints == ()

    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        Optional[DummyDataclass],  # noqa: UP045
        "field",
    )
    assert runtime_type is DummyDataclass
    assert constraints == ()


def test_extract_runtime_type_union_with_none() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        DummyDataclass | None, "field"
    )
    assert runtime_type is DummyDataclass
    assert constraints == ()

    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        Union[int, None],  # noqa: UP007
        "field",
    )
    assert runtime_type is int
    assert constraints == ()


def test_extract_runtime_type_annotated() -> None:
    annotated = Annotated[DummyDataclass, "metadata"]
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        annotated, "field"
    )
    assert runtime_type is DummyDataclass
    assert constraints == ()


def test_extract_runtime_type_annotated_optional() -> None:
    annotated = Annotated[int | None, "metadata"]
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        annotated, "field"
    )
    assert runtime_type is int
    assert constraints == ()


def test_extract_runtime_type_invalid_union() -> None:
    with pytest.raises(TypeError, match="unsupported union type"):
        extract_runtime_type_and_constraints(int | str, "field")

    with pytest.raises(TypeError, match="unsupported union type"):
        extract_runtime_type_and_constraints(int | DummyDataclass | None, "field")


def test_extract_runtime_type_literal() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        Literal[1, 2], "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf((1, 2)),))


def test_extract_runtime_type_optional_literal() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        Optional[Literal[1, 2]],  # noqa: UP045
        "field",
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf((1, 2)),))


def test_extract_runtime_type_literal_union_with_none() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        Literal["a", "b"] | None, "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf(("a", "b")),))


def test_extract_runtime_type_heterogeneous_literal() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        Literal[1, "a", 2.0, True], "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf((1, "a", 2.0, True)),))


def test_extract_runtime_type_enum() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        BaseEnum, "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf(("a", "b")),))


def test_extract_runtime_type_optional_enum() -> None:
    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        Optional[BaseEnum],  # noqa: UP045
        "field",
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf(("a", "b")),))


def test_extract_runtime_type_empty_enum() -> None:
    class EmptyEnum(Enum):
        pass

    with pytest.raises(TypeError, match="empty Enum"):
        extract_runtime_type_and_constraints(EmptyEnum, "field")


def test_extract_runtime_type_heterogeneous_enum() -> None:
    class HeterogeneousEnum(Enum):
        INT = 1
        STR = "text"
        FLOAT = 3.14

    runtime_type, constraints, _ = extract_runtime_type_and_constraints(
        HeterogeneousEnum, "field"
    )
    assert runtime_type is ENUMERATED_TYPE
    assert_constraints_equal(constraints, (OneOf((1, "text", 3.14)),))


def test_extract_runtime_type_only_none() -> None:
    with pytest.raises(TypeError, match="unsupported type annotation"):
        extract_runtime_type_and_constraints(None, "field")


def test_extract_runtime_type_unsupported_annotation() -> None:
    with pytest.raises(TypeError, match="unsupported type annotation"):
        extract_runtime_type_and_constraints(dict[str, int], "field")


def test_extract_runtime_type_email() -> None:
    assert extract_runtime_type_and_constraints(Email, "email") == (Email, (), None)


def test_basic_list() -> None:
    leaf, constraints, collection = extract_runtime_type_and_constraints(
        list[str], "tags"
    )
    assert leaf is str
    assert constraints == ()
    assert collection is list


def test_typing_list_alias() -> None:
    leaf, constraints, collection = extract_runtime_type_and_constraints(
        list[str], "items"
    )
    assert leaf is str
    assert constraints == ()
    assert collection is list


def test_list_with_annotated_element():
    leaf, constraints, collection = extract_runtime_type_and_constraints(
        list[Annotated[str, MinLength(5)]], "codes"
    )
    assert leaf is str
    assert len(constraints) == 1
    assert isinstance(constraints[0], MinLength)
    assert constraints[0].value == 5
    assert collection is list


def test_list_with_multiple_element_constraints():
    leaf, constraints, collection = extract_runtime_type_and_constraints(
        list[Annotated[str, MinLength(2), MaxLength(10)]], "short_ids"
    )
    assert leaf is str
    assert len(constraints) == 2
    assert collection is list


def test_list_email() -> None:
    leaf, constraints, collection = extract_runtime_type_and_constraints(
        list[Email], "emails"
    )
    assert leaf is Email
    assert len(constraints) == 0
    assert collection is list


# ====== TESTS FOR is_nullable() ======


def test_is_nullable_optional_str() -> None:
    assert is_nullable(str | None)


def test_is_nullable_optional_int() -> None:
    assert is_nullable(int | None)


def test_is_nullable_union_with_none() -> None:
    assert is_nullable(str | None)


def test_is_nullable_union_multiple_with_none() -> None:
    assert is_nullable(str | int | None)


def test_is_nullable_not_optional_str() -> None:
    assert not is_nullable(str)


def test_is_nullable_not_optional_int() -> None:
    assert not is_nullable(int)


def test_is_nullable_union_without_none() -> None:
    assert not is_nullable(str | int)


def test_is_nullable_list() -> None:
    assert not is_nullable(list)


def test_is_nullable_annotated_union() -> None:
    assert is_nullable(Annotated[int | None, "ge=0"])


def test_is_nullable_annotated_not_optional() -> None:
    assert not is_nullable(Annotated[int, "ge=0"])
