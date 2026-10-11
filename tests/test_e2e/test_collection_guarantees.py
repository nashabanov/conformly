from dataclasses import dataclass, make_dataclass
from typing import Annotated, Literal

import pytest

from conformly import (
    GreaterOrEqual,
    LessOrEqual,
    MaxItems,
    MinItems,
    MultipleOf,
    UniqueItems,
    case,
)
from conformly.exceptions import GenerationError, SchemaError


@pytest.mark.parametrize(
    "annotation", [list[int], set[int], frozenset[int], tuple[int, ...], dict[str, int]]
)
@pytest.mark.parametrize(
    "minimum,maximum",
    [(None, 0), (0, 0), (5, None), (1, 1), (20, 20), (21, 21), (25, 25)],
)
def test_public_collection_size_guarantees(annotation, minimum, maximum):
    constraints = []
    if minimum is not None:
        constraints.append(MinItems(minimum))
    if maximum is not None:
        constraints.append(MaxItems(maximum))
    model = make_dataclass("Sized", [("items", Annotated[annotation, *constraints])])
    for seed in (0, 42, -1):
        items = case(model, seed=seed)["items"]
        assert len(items) >= (minimum or 0)
        if maximum is not None:
            assert len(items) <= maximum
        if annotation in (set[int], frozenset[int]):
            assert isinstance(items, list)
            assert len(set(items)) == len(items)


@pytest.mark.parametrize("size", [0, 1, 20, 21, 25])
def test_public_unique_integer_lists_fill_exact_size(size):
    model = make_dataclass(
        "Unique",
        [
            (
                "items",
                Annotated[
                    list[Annotated[int, GreaterOrEqual(0), LessOrEqual(24)]],
                    MinItems(size),
                    MaxItems(size),
                    UniqueItems(True),
                ],
            )
        ],
    )
    for seed in (0, 42, -1):
        items = case(model, seed=seed)["items"]
        assert len(items) == size
        assert len(set(items)) == size
        assert all(0 <= item <= 24 for item in items)


@dataclass
class Record:
    number: int


@dataclass
class UniqueRecords:
    records: Annotated[list[Record], MinItems(25), MaxItems(25), UniqueItems(True)]


def test_nested_records_are_structurally_unique():
    items = case(UniqueRecords, seed=42)["records"]
    assert len(items) == 25
    assert all(
        isinstance(item, dict) and isinstance(item["number"], int) for item in items
    )
    assert all(item not in items[:i] for i, item in enumerate(items))


@dataclass
class RecordMapping:
    records: Annotated[dict[str, Record], MinItems(25), MaxItems(25)]


def test_nested_dictionary_values_preserve_collection_size():
    items = case(RecordMapping, seed=42)["records"]
    assert len(items) == 25
    assert all(
        isinstance(item, dict) and isinstance(item["number"], int)
        for item in items.values()
    )


@pytest.mark.parametrize(
    "annotation,unique",
    [
        (list[bool], True),
        (set[bool], False),
        (frozenset[bool], False),
        (dict[Literal["a", "b"], int], False),
    ],
)
def test_impossible_finite_collection_size_fails_explicitly(annotation, unique):
    constraints = (MinItems(3), UniqueItems(True)) if unique else (MinItems(3),)
    model = make_dataclass(
        "Impossible", [("items", Annotated[annotation, *constraints])]
    )
    with pytest.raises(GenerationError) as exc:
        case(model, seed=0)
    assert exc.value.context["code"] == "impossible_collection_size"
    assert exc.value.context["requested_size"] == 3
    assert exc.value.context["cardinality"] == 2


@pytest.mark.parametrize("annotation", [list[int], dict[str, int], tuple[int, ...]])
def test_positive_minimum_with_zero_maximum_is_rejected(annotation):
    model = make_dataclass(
        "Impossible",
        [
            (
                "items",
                Annotated[
                    annotation,
                    MinItems(1),
                    MaxItems(0),
                ],
            )
        ],
    )
    with pytest.raises(SchemaError) as exc:
        case(model)
    assert exc.value.context["code"] == "invalid_length_range"


@pytest.mark.parametrize("seed", range(10))
def test_optional_finite_domain_sizes_are_capped(seed):
    model = make_dataclass(
        "Finite",
        [
            ("flags", set[bool]),
            ("mapping", dict[Literal["a", "b"], int]),
        ],
    )
    result = case(model, seed=seed)
    assert 1 <= len(result["flags"]) <= 2
    assert len(set(result["flags"])) == len(result["flags"])
    assert 1 <= len(result["mapping"]) <= 2


@pytest.mark.parametrize("size", [1, 2, 3])
def test_integer_multiple_domain_has_enough_unique_values(size):
    model = make_dataclass(
        "Multiples",
        [
            (
                "items",
                Annotated[
                    list[
                        Annotated[
                            int, GreaterOrEqual(-2), LessOrEqual(2), MultipleOf(2)
                        ]
                    ],
                    MinItems(size),
                    MaxItems(size),
                    UniqueItems(True),
                ],
            )
        ],
    )
    result = case(model, seed=42)["items"]
    assert len(result) == size
    assert len(set(result)) == size
    assert set(result) <= {-2, 0, 2}


def test_integer_multiple_domain_rejects_impossible_size():
    model = make_dataclass(
        "Multiples",
        [
            (
                "items",
                Annotated[
                    list[
                        Annotated[
                            int, GreaterOrEqual(-2), LessOrEqual(2), MultipleOf(2)
                        ]
                    ],
                    MinItems(4),
                    UniqueItems(True),
                ],
            )
        ],
    )
    with pytest.raises(GenerationError) as exc:
        case(model)
    assert exc.value.context["code"] == "impossible_collection_size"
    assert exc.value.context["cardinality"] == 3


@dataclass
class SingletonRecord:
    number: Literal[1]


@dataclass
class ImpossibleRecords:
    records: Annotated[list[SingletonRecord], MinItems(2), UniqueItems(True)]


def test_public_structural_duplicates_fail_instead_of_returning_short_list():
    with pytest.raises(GenerationError) as exc:
        case(ImpossibleRecords, seed=0)
    assert exc.value.context["code"] == "collection_retry_exhausted"
    assert exc.value.context["requested_size"] >= 2
    assert exc.value.context["generated_size"] == 1
