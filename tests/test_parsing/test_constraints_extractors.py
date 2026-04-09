from dataclasses import dataclass, field, fields
from typing import Annotated

import pytest

from conformly._internal.constraints import (
    Constraint,
    GreaterOrEqual,
    MinLength,
    OneOf,
    Pattern,
)
from conformly._internal.parsing.extractors.constraints import (
    _metadata_to_constraints,
    is_constraints_consistent,
    parse_annotated_constraints,
    parse_metadata_constraints,
)


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
    with pytest.raises(ValueError, match="Unknown constraint type 'unknown'"):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError, match="Unknown constraint type"):
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
