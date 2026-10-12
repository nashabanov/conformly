from dataclasses import make_dataclass
from typing import Annotated, TypedDict

import pytest

from conformly import MaxLength, MinItems, MinLength, UniqueItems, V, case, cases, path
from conformly.exceptions import GenerationError, PlanningError


@pytest.mark.parametrize("adapter", ["dataclass", "typeddict", "attrs", "pydantic"])
def test_bytes_across_adapters(adapter):
    annotation = Annotated[bytes, MinLength(2), MaxLength(5)]
    if adapter == "dataclass":
        model = make_dataclass(
            "Payload", [("value", annotation), ("other", annotation)]
        )
    elif adapter == "typeddict":

        class Payload(TypedDict):
            value: annotation
            other: annotation

        model = Payload
    elif adapter == "attrs":
        attrs = pytest.importorskip("attrs")
        model = attrs.make_class(
            "Payload",
            {
                "value": attrs.field(type=annotation),
                "other": attrs.field(type=annotation),
            },
        )
    else:
        pydantic = pytest.importorskip("pydantic")
        model = pydantic.create_model(
            "Payload",
            value=(bytes, pydantic.Field(min_length=2, max_length=5)),
            other=(bytes, pydantic.Field(min_length=2, max_length=5)),
        )
    for seed in (0, 1, -1):
        payload = case(model, seed=seed)
        assert type(payload["value"]) is bytes
        assert 2 <= len(payload["value"]) <= 5
        assert payload == case(model, seed=seed)
        if adapter == "pydantic":
            model.model_validate(payload)
    for violation, length in ((V.TOO_SHORT, 1), (V.TOO_LONG, 6)):
        payload = case(model, valid=False, strategy=path("value").violate(violation))
        assert type(payload["value"]) is bytes
        assert len(payload["value"]) == length
        assert 2 <= len(payload["other"]) <= 5
        if adapter == "pydantic":
            with pytest.raises(pydantic.ValidationError):
                model.model_validate(payload)
    payload = case(
        model,
        valid=False,
        strategy=path("value").violate(V.TYPE_MISMATCH),
        allow_type_mismatch=True,
    )
    assert type(payload["value"]) is int
    assert type(payload["other"]) is bytes
    missing = cases(
        model, valid=False, strategy="all", allow_structural_violations=True
    )[0]
    assert "value" not in missing
    assert type(missing["other"]) is bytes


@pytest.mark.parametrize("constraints", [(), (MaxLength(0),), (MinLength(1),)])
def test_unconstrained_empty_and_minimum_only(constraints):
    annotation = Annotated[bytes, *constraints] if constraints else bytes
    model = make_dataclass("Payload", [("value", annotation)])
    value = case(model, seed=0)["value"]
    assert type(value) is bytes
    if constraints == (MaxLength(0),):
        assert value == b""
        assert (
            case(model, valid=False, strategy=path("value").violate(V.TOO_LONG))[
                "value"
            ]
            != b""
        )
    elif constraints:
        assert len(value) >= 1
    with pytest.raises(PlanningError):
        case(model, valid=False, strategy=path("value").violate(V.PATTERN_MISMATCH))


@pytest.mark.parametrize("collection", [list, set, frozenset, tuple])
def test_bytes_in_collections(collection):
    item = Annotated[bytes, MinLength(2), MaxLength(5)]
    annotation = collection[item, ...] if collection is tuple else collection[item]
    model = make_dataclass("Payload", [("value", annotation)])
    payload = case(model, seed=0)
    assert all(
        type(value) is bytes and 2 <= len(value) <= 5 for value in payload["value"]
    )
    invalid = case(model, valid=False, strategy=path("value").violate(V.TOO_SHORT))
    assert sum(len(value) == 1 for value in invalid["value"]) == 1
    assert all(1 <= len(value) <= 5 for value in invalid["value"])


def test_nested_bytes_inside_dictionary_values():
    child = make_dataclass("Child", [("value", Annotated[bytes, MinLength(2)])])
    parent = make_dataclass(
        "Parent", [("children", dict[str, child]), ("other", bytes)]
    )
    payload = case(
        parent, valid=False, strategy=path("children.value").violate(V.TOO_SHORT)
    )
    assert sum(len(child["value"]) == 1 for child in payload["children"].values()) == 1
    assert type(payload["other"]) is bytes


def test_empty_bytes_have_one_distinct_value():
    item = Annotated[bytes, MaxLength(0)]
    model = make_dataclass(
        "Payload", [("value", Annotated[list[item], MinItems(2), UniqueItems(True)])]
    )
    with pytest.raises(GenerationError):
        case(model)


def test_all_length_violations_on_dictionary_values():
    item = Annotated[bytes, MinLength(2), MaxLength(4)]
    model = make_dataclass("Payload", [("values", dict[str, item])])
    payloads = cases(model, valid=False, strategy="all_violations", seed=0)
    assert len(payloads) == 2
    assert sorted(
        len(value)
        for payload in payloads
        for value in payload["values"].values()
        if not 2 <= len(value) <= 4
    ) == [1, 5]
    assert all(
        type(value) is bytes
        for payload in payloads
        for value in payload["values"].values()
    )


def test_too_short_not_available_for_empty_bytes():
    model = make_dataclass("Empty", [("value", Annotated[bytes, MaxLength(0)])])
    with pytest.raises(PlanningError):
        case(model, valid=False, strategy=path("value").violate(V.TOO_SHORT))
