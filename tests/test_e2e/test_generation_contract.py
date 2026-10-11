"""A small adapter matrix with an oracle independent of conformly internals."""

from dataclasses import make_dataclass
import math
import re
from typing import Annotated, Literal, TypedDict

import pytest

from conformly import (
    GreaterOrEqual,
    LessOrEqual,
    MaxItems,
    MaxLength,
    MinItems,
    MinLength,
    MultipleOf,
    Pattern,
    V,
    case,
    cases,
    path,
)


@pytest.fixture(params=["dataclass", "typeddict", "pydantic", "attrs"])
def contract_model(request):
    adapter = request.param
    if adapter == "pydantic":
        pydantic = pytest.importorskip("pydantic")

        def annotation(kind, constraints):
            return Annotated[kind, pydantic.Field(**constraints)]

        def build(name, fields):
            return pydantic.create_model(
                name,
                __config__=pydantic.ConfigDict(extra="forbid"),
                **{key: (value, ...) for key, value in fields.items()},
            )
    else:
        constraints_by_name = {
            "ge": GreaterOrEqual,
            "le": LessOrEqual,
            "multiple_of": MultipleOf,
            "min_length": MinLength,
            "max_length": MaxLength,
            "pattern": Pattern,
        }

        def annotation(kind, constraints):
            collection = kind == list[int] or getattr(kind, "__origin__", None) is list
            metadata = [
                (MinItems(value) if key == "min_length" else MaxItems(value))
                if collection and key in ("min_length", "max_length")
                else constraints_by_name[key](value)
                for key, value in constraints.items()
            ]
            return Annotated[kind, *metadata]

        if adapter == "dataclass":

            def build(name, fields):
                return make_dataclass(name, list(fields.items()))
        elif adapter == "typeddict":

            def build(name, fields):
                return TypedDict(name, fields)
        else:
            attrs = pytest.importorskip("attrs")

            def build(name, fields):
                return attrs.make_class(
                    name,
                    {key: attrs.field(type=value) for key, value in fields.items()},
                )

    child = build(
        "ContractChild",
        {
            "score": annotation(int, {"ge": 1, "le": 3}),
        },
    )
    model = build(
        "ContractModel",
        {
            "number": annotation(int, {"ge": 2, "le": 12, "multiple_of": 2}),
            "ratio": annotation(float, {"ge": 0.25, "le": 1, "multiple_of": 0.25}),
            "text": annotation(
                str, {"min_length": 2, "max_length": 5, "pattern": "^a{1,6}$"}
            ),
            "choice": Literal["red", "blue"],
            "nested": child,
            "items": annotation(list[int], {"min_length": 2, "max_length": 3}),
            "records": annotation(list[child], {"min_length": 1, "max_length": 2}),
        },
    )
    return adapter, model


EXPECTED = {
    ("number", V.BELOW_MIN),
    ("number", V.ABOVE_MAX),
    ("number", V.NOT_MULTIPLE),
    ("ratio", V.BELOW_MIN),
    ("ratio", V.ABOVE_MAX),
    ("ratio", V.NOT_MULTIPLE),
    ("text", V.TOO_SHORT),
    ("text", V.TOO_LONG),
    ("text", V.PATTERN_MISMATCH),
    ("choice", V.NOT_ALLOWED_VALUE),
    ("nested.score", V.BELOW_MIN),
    ("nested.score", V.ABOVE_MAX),
    ("items", V.TOO_LESS_ITEMS),
    ("items", V.TOO_MANY_ITEMS),
    ("records", V.TOO_LESS_ITEMS),
    ("records", V.TOO_MANY_ITEMS),
    ("records.score", V.BELOW_MIN),
    ("records.score", V.ABOVE_MAX),
}


def violations(payload):
    """Check concrete values, never resolver/planner output or generator helpers."""
    failures = set()

    def check(target, violation, condition):
        if condition:
            failures.add((target, violation))

    def numeric(target, value, low, high, divisor=None):
        assert isinstance(value, (int, float)) and not isinstance(value, bool)
        assert math.isfinite(value)
        check(target, V.BELOW_MIN, value < low)
        check(target, V.ABOVE_MAX, value > high)
        if divisor is not None:
            quotient = value / divisor
            check(target, V.NOT_MULTIPLE, abs(quotient - round(quotient)) > 1e-9)

    assert set(payload) == {
        "number",
        "ratio",
        "text",
        "choice",
        "nested",
        "items",
        "records",
    }
    assert isinstance(payload["number"], int)
    assert isinstance(payload["ratio"], float)
    numeric("number", payload["number"], 2, 12, 2)
    numeric("ratio", payload["ratio"], 0.25, 1, 0.25)
    text = payload["text"]
    assert isinstance(text, str)
    check("text", V.TOO_SHORT, len(text) < 2)
    check("text", V.TOO_LONG, len(text) > 5)
    check("text", V.PATTERN_MISMATCH, re.search("^a{1,6}$", text) is None)
    check("choice", V.NOT_ALLOWED_VALUE, payload["choice"] not in ("red", "blue"))
    assert set(payload["nested"]) == {"score"}
    numeric("nested.score", payload["nested"]["score"], 1, 3)
    for name, minimum, maximum in (("items", 2, 3), ("records", 1, 2)):
        values = payload[name]
        assert isinstance(values, list)
        check(name, V.TOO_LESS_ITEMS, len(values) < minimum)
        check(name, V.TOO_MANY_ITEMS, len(values) > maximum)
        for value in values:
            if name == "items":
                assert isinstance(value, int) and not isinstance(value, bool)
            else:
                assert set(value) == {"score"}
                numeric("records.score", value["score"], 1, 3)
    return failures


def validate_framework(adapter, model, payload, valid):
    if adapter == "pydantic":
        if valid:
            model.model_validate(payload)
        else:
            pydantic = pytest.importorskip("pydantic")
            with pytest.raises(pydantic.ValidationError):
                model.model_validate(payload)


@pytest.mark.parametrize("seed", [0, 7])
@pytest.mark.parametrize("api", [case, cases])
def test_valid_contract(contract_model, seed, api, capsys):
    adapter, model = contract_model
    kwargs = {"seed": seed, "valid": True}
    if api is cases:
        kwargs["count"] = 3
    result = api(model, **kwargs)
    payloads = result if api is cases else [result]
    for payload in payloads:
        assert not violations(payload)
        validate_framework(adapter, model, payload, valid=True)
    assert api(model, **kwargs) == result
    assert capsys.readouterr().out == ""


# Cover scalar, nested object, collection size and nested collection targeting,
# without taking a Cartesian product of every violation and option.
@pytest.mark.parametrize(
    "target,violation,api,seed",
    [
        ("number", V.NOT_MULTIPLE, case, 0),
        ("text", V.PATTERN_MISMATCH, cases, 7),
        ("nested.score", V.ABOVE_MAX, case, 7),
        ("items", V.TOO_LESS_ITEMS, cases, 0),
        ("records.score", V.BELOW_MIN, case, 0),
    ],
)
def test_explicit_target_contract(contract_model, target, violation, api, seed, capsys):
    adapter, model = contract_model
    result = api(
        model, valid=False, seed=seed, strategy=path(target).violate(violation)
    )
    payloads = result if api is cases else [result]
    for payload in payloads:
        failures = violations(payload)
        assert (target, violation) in failures
        assert {name for name, _ in failures} == {target}
        if target == "records.score":
            assert (
                sum(not 1 <= record["score"] <= 3 for record in payload["records"]) == 1
            )
        validate_framework(adapter, model, payload, valid=False)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("strategy,seed", [("all", 0), ("all_violations", 7)])
def test_automatic_violation_coverage(contract_model, strategy, seed, capsys):
    adapter, model = contract_model
    observed = set()
    for payload in cases(model, valid=False, seed=seed, strategy=strategy):
        failures = violations(payload)
        assert failures
        assert len({name for name, _ in failures}) == 1
        observed.update(failures)
        validate_framework(adapter, model, payload, valid=False)
    if strategy == "all_violations":
        assert observed >= EXPECTED
    else:
        assert {name for name, _ in observed} == {name for name, _ in EXPECTED}
    assert capsys.readouterr().out == ""
