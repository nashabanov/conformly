from dataclasses import dataclass, make_dataclass
from typing import Annotated, Literal

import pytest

from conformly import (
    GreaterOrEqual,
    MaxItems,
    MinItems,
    MinLength,
    UniqueItems,
    V,
    case,
    cases,
    path,
)
from conformly.exceptions import PlanningError

SizedKey = Annotated[str, MinLength(3)]
BoundedValue = Annotated[int, GreaterOrEqual(10)]


@pytest.mark.parametrize(
    "annotation,violation,side",
    [
        (dict[SizedKey, int], V.TOO_SHORT, "key"),
        (dict[str, BoundedValue], V.BELOW_MIN, "value"),
        (dict[SizedKey, BoundedValue], V.TOO_SHORT, "key"),
        (dict[SizedKey, BoundedValue], V.BELOW_MIN, "value"),
    ],
)
@pytest.mark.parametrize("seed", [0, 1, 42, -1])
def test_dictionary_violations_route_to_applicable_side(
    annotation, violation, side, seed
):
    model = make_dataclass(
        "Mapping",
        [
            ("items", Annotated[annotation, MinItems(3), MaxItems(3)]),
            ("safe", Annotated[str, MinLength(5)]),
        ],
    )
    selector = path(model, lambda m: m.items).violate(violation)
    result = case(model, valid=False, strategy=selector, seed=seed)
    assert len(result["safe"]) >= 5
    items = result["items"]
    assert len(items) == 3
    if side == "key":
        assert sum(len(key) < 3 for key in items) == 1
        assert all(isinstance(value, int) for value in items.values())
        if annotation == dict[SizedKey, BoundedValue]:
            assert all(value >= 10 for value in items.values())
    else:
        assert sum(value < 10 for value in items.values()) == 1
        if annotation == dict[SizedKey, BoundedValue]:
            assert all(len(key) >= 3 for key in items)


@dataclass
class MixedTuple:
    items: tuple[str, BoundedValue, SizedKey]
    safe: Annotated[int, GreaterOrEqual(100)]


@pytest.mark.parametrize("violation,index", [(V.BELOW_MIN, 1), (V.TOO_SHORT, 2)])
@pytest.mark.parametrize("seed", [0, 42, -1])
def test_fixed_tuple_targets_compatible_element_and_keeps_order(violation, index, seed):
    result = case(
        MixedTuple, valid=False, strategy=f"items::{violation.value}", seed=seed
    )
    items = result["items"]
    assert isinstance(items, tuple) and len(items) == 3
    assert isinstance(items[0], str)
    assert isinstance(items[1], int)
    assert isinstance(items[2], str)
    assert result["safe"] >= 100
    if index == 1:
        assert items[1] < 10
        assert len(items[2]) >= 3
    else:
        assert items[1] >= 10
        assert len(items[2]) < 3


@pytest.mark.parametrize(
    "annotation", [list[BoundedValue], set[BoundedValue], tuple[BoundedValue, ...]]
)
def test_one_collection_element_is_invalid_and_others_are_valid(annotation):
    model = make_dataclass(
        "Elements",
        [
            ("items", Annotated[annotation, MinItems(3), MaxItems(3)]),
            ("safe", SizedKey),
        ],
    )
    result = case(model, valid=False, strategy="items::below_min", seed=42)
    assert len(result["items"]) == 3
    assert sum(value < 10 for value in result["items"]) == 1
    assert len(result["safe"]) >= 3
    if annotation == set[BoundedValue]:
        assert len(set(result["items"])) == 3


@pytest.mark.parametrize(
    "annotation",
    [
        list[SizedKey],
        tuple[SizedKey, ...],
        dict[SizedKey, BoundedValue],
    ],
)
def test_empty_only_collection_rejects_element_target_and_supports_size_target(
    annotation,
):
    model = make_dataclass("Empty", [("items", Annotated[annotation, MaxItems(0)])])
    with pytest.raises(PlanningError):
        case(model, valid=False, strategy="items::too_short")
    result = case(model, valid=False, strategy="items::too_many_items", seed=0)
    assert len(result["items"]) == 1
    if isinstance(result["items"], dict):
        assert all(
            len(key) >= 3 and value >= 10 for key, value in result["items"].items()
        )
    else:
        assert all(len(item) >= 3 for item in result["items"])


@pytest.mark.parametrize("annotation", [list[int], set[int], frozenset[int]])
@pytest.mark.parametrize("size", [2, 3, 25])
def test_duplicate_violation_preserves_allowed_exact_size(annotation, size):
    model = make_dataclass(
        "Duplicate",
        [
            (
                "items",
                Annotated[
                    annotation,
                    MinItems(size),
                    MaxItems(size),
                    UniqueItems(True),
                ],
            )
        ],
    )
    items = case(model, valid=False, strategy="items::duplicate", seed=0)["items"]
    assert len(items) == size
    assert len(set(items)) < size
    assert all(isinstance(item, int) for item in items)


@dataclass
class Singleton:
    value: Literal[1]


@dataclass
class DuplicateObjects:
    items: Annotated[list[Singleton], MinItems(2), MaxItems(2), UniqueItems(True)]


def test_duplicate_nested_objects_need_no_feasible_unique_base():
    assert case(DuplicateObjects, valid=False, strategy="items::duplicate", seed=0)[
        "items"
    ] == [{"value": 1}, {"value": 1}]


@pytest.mark.parametrize(
    "violation,size", [(V.TOO_LESS_ITEMS, 2), (V.TOO_MANY_ITEMS, 4)]
)
def test_dictionary_size_violation_counts_distinct_keys(violation, size):
    model = make_dataclass(
        "SizedMapping",
        [
            (
                "items",
                Annotated[
                    dict[Literal["a", "b", "c", "d"], BoundedValue],
                    MinItems(3),
                    MaxItems(3),
                ],
            )
        ],
    )
    result = case(model, valid=False, strategy=f"items::{violation.value}", seed=42)[
        "items"
    ]
    assert len(result) == size
    assert set(result) <= {"a", "b", "c", "d"}
    assert all(value >= 10 for value in result.values())


def test_impossible_explicit_dictionary_size_target_does_not_substitute_violation():
    model = make_dataclass(
        "Finite",
        [
            (
                "items",
                Annotated[
                    dict[Literal["a", "b"], int],
                    MinItems(2),
                    MaxItems(2),
                ],
            )
        ],
    )
    with pytest.raises(PlanningError):
        case(model, valid=False, strategy="items::too_many_items")


def test_all_violations_keeps_dictionary_routes():
    model = make_dataclass(
        "Mapping",
        [
            (
                "items",
                Annotated[
                    dict[SizedKey, BoundedValue],
                    MinItems(3),
                    MaxItems(3),
                ],
            )
        ],
    )
    results = cases(model, valid=False, strategy="all_violations", seed=42)
    assert len(results) == 4
    assert len(results[0]["items"]) == 2
    assert len(results[1]["items"]) == 4
    assert sum(v < 10 for v in results[2]["items"].values()) == 1
    assert all(len(k) >= 3 for k in results[2]["items"])
    assert sum(len(k) < 3 for k in results[3]["items"]) == 1
    assert all(v >= 10 for v in results[3]["items"].values())


@dataclass
class NestedRecord:
    number: BoundedValue
    safe: SizedKey


@pytest.mark.parametrize(
    "annotation", [list[NestedRecord], set[NestedRecord], dict[SizedKey, NestedRecord]]
)
def test_nested_collection_field_target_preserves_shape_and_unrelated_elements(
    annotation,
):
    model = make_dataclass(
        "Nested",
        [
            ("items", Annotated[annotation, MinItems(3), MaxItems(3)]),
            ("safe", SizedKey),
        ],
    )
    result = case(model, valid=False, strategy="items.number::below_min", seed=42)
    items = result["items"]
    assert len(items) == 3
    if isinstance(items, dict):
        assert all(len(key) >= 3 for key in items)
        values = list(items.values())
    else:
        values = items
    assert sum(item["number"] < 10 for item in values) == 1
    assert all(len(item["safe"]) >= 3 for item in values)
    assert len(result["safe"]) >= 3
    if annotation == set[NestedRecord]:
        assert all(item not in values[:i] for i, item in enumerate(values))


@pytest.mark.parametrize("annotation", [list[NestedRecord], dict[str, NestedRecord]])
def test_empty_only_nested_collection_does_not_offer_nested_field_targets(annotation):
    model = make_dataclass(
        "EmptyNested", [("items", Annotated[annotation, MaxItems(0)])]
    )
    with pytest.raises(PlanningError):
        case(model, valid=False, strategy="items.number::below_min")
    results = cases(model, valid=False, strategy="all_violations", seed=42)
    assert len(results) == 1
    assert len(results[0]["items"]) == 1


@dataclass
class SingletonUnique:
    items: Annotated[list[Singleton], MinItems(2), MaxItems(2), UniqueItems(True)]


def test_nested_field_invalidation_does_not_require_a_valid_unique_target():
    items = case(
        SingletonUnique, valid=False, strategy="items.value::not_allowed_value", seed=0
    )["items"]
    assert len(items) == 2
    assert items[0]["value"] != 1
    assert items[1]["value"] == 1


@pytest.mark.parametrize(
    "annotation",
    [
        Annotated[list[Literal["a", "b"]], UniqueItems(True)],
        dict[Literal["a", "b"], BoundedValue],
    ],
)
def test_invalid_target_can_add_one_value_outside_finite_domain(annotation):
    model = make_dataclass(
        "Finite", [("items", Annotated[annotation, MinItems(3), MaxItems(3)])]
    )
    result = case(model, valid=False, strategy="items::not_allowed_value", seed=42)[
        "items"
    ]
    assert len(result) == 3
    assert len(set(result)) == 3
    assert sum(value not in ("a", "b") for value in result) == 1
    if isinstance(result, dict):
        assert all(value >= 10 for value in result.values())
