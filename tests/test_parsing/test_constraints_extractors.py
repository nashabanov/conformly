from dataclasses import dataclass, field, fields
from typing import Annotated, Any

import pytest

from conformly._internal.constraints import (
    Constraint,
    ConstraintType,
    GreaterOrEqual,
    MinLength,
    OneOf,
    Pattern,
)
from conformly._internal.parser.extractors.constraints import (
    _coerce_constraint_value,
    _metadata_to_constraints,
    is_constraints_consistent,
    parse_annotated_constraints,
    parse_metadata_constraints,
)
from conformly.exceptions import SchemaError


@dataclass
class DummyDataclass:
    name: str
    age: int


@dataclass
class ConstraintsDataclass:
    age: Annotated[int, "ge=0", "le=150"]
    email: Annotated[str, "pattern=^\\w+@\\w+\\.\\w+$"]
    tags: list = field(metadata={"min_length": 1, "max_length": 10})


# ====== TESTS FOR parse_annotated_constraints() ======


def test_parse_annotated_constraints_exists():
    constraints = parse_annotated_constraints(Annotated[int, "ge=0", "le=150"])
    assert len(constraints) == 2
    for c in constraints:
        assert isinstance(c, Constraint)


def test_parse_annotated_constraints_empty():
    constraints = parse_annotated_constraints(str)
    assert constraints == ()


def test_parse_annotated_constraints_single():
    constraints = parse_annotated_constraints(Annotated[str, "pattern=^\\w+$"])
    assert len(constraints) == 1


def test_parse_annotated_constraints_none():
    constraints = parse_annotated_constraints(type(None))
    assert constraints == ()


def test_parse_annotated_constraints_dict_format_valid():
    constraints = parse_annotated_constraints(
        Annotated[str, {"type": "pattern", "value": "^\\w+$"}]
    )
    assert len(constraints) == 1
    assert isinstance(constraints[0], Pattern)
    assert constraints[0].regex == "^\\w+$"


def test_parse_annotated_constraints_dict_format_invalid_key():
    with pytest.raises(SchemaError):
        parse_annotated_constraints(Annotated[str, {"type": "unknown", "value": "x"}])


# ====== TESTS FOR parse_metadata_constraints() ======


def test_parse_metadata_constraints_exists():
    f = fields(ConstraintsDataclass)[2]  # tags field
    constraints = parse_metadata_constraints(f.metadata)
    assert len(constraints) > 0
    for c in constraints:
        assert isinstance(c, Constraint)


def test_parse_metadata_constraints_empty():
    f = fields(DummyDataclass)[0]
    constraints = parse_metadata_constraints(f.metadata)
    assert constraints == ()


def test_parse_metadata_constraints_custom_keys():
    @dataclass
    class CustomMetadata:
        value: int = field(metadata={"custom_key": "custom_value"})

    f = fields(CustomMetadata)[0]
    with pytest.raises(SchemaError):
        parse_metadata_constraints(f.metadata)


def test_parse_metadata_constraints_ignored_private():
    @dataclass
    class PrivateMeta:
        x: int = field(metadata={"_internal": "ignored", "min_length": 1})

    f = fields(PrivateMeta)[0]
    constraints = parse_metadata_constraints(f.metadata)
    assert len(constraints) == 1
    assert isinstance(constraints[0], MinLength)


def test_parse_metadata_constraints_invalid_constraint_type():
    @dataclass
    class BadMeta:
        x: int = field(metadata={"invalid_key": 42})

    f = fields(BadMeta)[0]
    with pytest.raises(SchemaError):
        parse_metadata_constraints(f.metadata)


def test_metadata_to_constraints_constraint_spec_direct():
    cs = MinLength(0)
    result = _metadata_to_constraints(cs)
    assert result is cs


def test_metadata_to_constraints_unsupported_type():
    assert _metadata_to_constraints(42) is None
    assert _metadata_to_constraints([1, 2]) is None


# ===== TESTS for is_constraints_consistent() =====


def test_is_constraints_consistent_valid():
    constraints = (OneOf((1, 2)),)
    assert is_constraints_consistent(constraints)


def test_is_constraints_consistent_invalid():
    constraints = (OneOf((1, 2)), GreaterOrEqual(1))
    assert not is_constraints_consistent(constraints)


# ====== TESTS for _coerce_constraint_value() =====


@pytest.mark.parametrize(
    "value, expected",
    [
        ("hello", "hello"),
        (123, "123"),
        (3.14, "3.14"),
        (None, "None"),
        (True, "True"),
    ],
)
def test_pattern_coerces_to_string(value: Any, expected: str) -> None:
    assert _coerce_constraint_value("pattern", value) == expected


@pytest.mark.parametrize("constraint", ["min_length", "max_length"])
def test_string_constraints_accept_valid_int_and_str(
    constraint: ConstraintType,
) -> None:
    assert _coerce_constraint_value(constraint, 5) == 5
    assert _coerce_constraint_value(constraint, "  10  ") == 10
    assert _coerce_constraint_value(constraint, "-1") == -1


@pytest.mark.parametrize("constraint", ["min_length", "max_length"])
def test_string_constraints_reject_non_numeric_str(constraint: ConstraintType) -> None:
    with pytest.raises(SchemaError):
        _coerce_constraint_value(constraint, "abc")


@pytest.mark.parametrize("constraint", ["min_length", "max_length"])
def test_string_constraints_reject_float(constraint: ConstraintType) -> None:
    with pytest.raises(SchemaError):
        _coerce_constraint_value(constraint, 1.5)


@pytest.mark.parametrize("constraint", ["gt", "ge", "lt", "le", "multiple_of"])
def test_numeric_constraints_accept_valid(constraint: ConstraintType) -> None:
    assert _coerce_constraint_value(constraint, 5) == 5
    assert _coerce_constraint_value(constraint, 2.5) == 2.5
    assert _coerce_constraint_value(constraint, " -4 ") == -4
    assert _coerce_constraint_value(constraint, " 0.75 ") == 0.75
    assert _coerce_constraint_value(constraint, "1e2") == 100.0


@pytest.mark.parametrize("constraint", ["gt", "ge", "lt", "le", "multiple_of"])
def test_numeric_constraints_reject_invalid_str(constraint: ConstraintType) -> None:
    with pytest.raises(SchemaError):
        _coerce_constraint_value(constraint, "abc")


@pytest.mark.parametrize("constraint", ["min_items", "max_items"])
def test_collection_constraints_accept_valid(constraint: ConstraintType) -> None:
    assert _coerce_constraint_value(constraint, 3) == 3
    assert _coerce_constraint_value(constraint, " 5 ") == 5


@pytest.mark.parametrize("constraint", ["min_items", "max_items"])
def test_collection_constraints_reject_bool(constraint: ConstraintType) -> None:
    with pytest.raises(SchemaError):
        _coerce_constraint_value(constraint, True)


@pytest.mark.parametrize("constraint", ["min_items", "max_items"])
def test_collection_constraints_reject_float_and_other(
    constraint: ConstraintType,
) -> None:
    with pytest.raises(SchemaError):
        _coerce_constraint_value(constraint, 2.5)
    with pytest.raises(SchemaError):
        _coerce_constraint_value(constraint, [1, 2])


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("true", True),
        (" 1 ", True),
        ("YES", True),
        ("false", False),
        ("0", False),
        ("no", False),
        (1, True),
        (0, False),
        (-5, True),
        (0.0, False),
        (0.1, True),
    ],
)
def test_unique_items_coerces_various_types(
    value: tuple[Any, ...], expected: tuple[Any, ...]
) -> None:
    assert _coerce_constraint_value("unique_items", value) is expected


def test_unique_items_rejects_unsupported_type() -> None:
    with pytest.raises(SchemaError):
        _coerce_constraint_value("unique_items", object())
