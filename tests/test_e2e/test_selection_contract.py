"""Public selection options, including eligibility before violation planning."""

from dataclasses import dataclass, make_dataclass
from random import Random
from typing import Annotated, NotRequired, TypedDict

import pytest

from conformly import MinLength, V, case, cases, path
from conformly.exceptions import GenerationError, PlanningError
from conformly.tracer import Tracer


@pytest.fixture(params=["dataclass", "typeddict", "pydantic", "attrs"])
def selection_model(request):
    text = Annotated[str, MinLength(3)]
    if request.param == "dataclass":
        return make_dataclass(
            "Selection", [("text", text), ("flag", bool), ("optional", bool, False)]
        )
    if request.param == "typeddict":
        return TypedDict(
            "Selection", {"text": text, "flag": bool, "optional": NotRequired[bool]}
        )
    if request.param == "pydantic":
        pydantic = pytest.importorskip("pydantic")
        return pydantic.create_model(
            "Selection",
            text=(str, pydantic.Field(min_length=3)),
            flag=(bool, ...),
            optional=(bool, False),
        )
    attrs = pytest.importorskip("attrs")
    return attrs.make_class(
        "Selection",
        {
            "text": attrs.field(type=text),
            "flag": attrs.field(type=bool),
            "optional": attrs.field(type=bool, default=False),
        },
    )


@pytest.mark.parametrize(
    "api,strategy",
    [
        (case, "first"),
        (case, "random"),
        (cases, "first"),
        (cases, "random"),
        (cases, "all"),
        (cases, "all_violations"),
    ],
)
@pytest.mark.parametrize("seed", [0, 7, -1])
def test_supported_strategies(selection_model, api, strategy, seed):
    result = api(selection_model, valid=False, strategy=strategy, seed=seed)
    assert result == api(selection_model, valid=False, strategy=strategy, seed=seed)
    payloads = result if api is cases else [result]
    assert len(payloads) == 1
    assert len(payloads[0]["text"]) < 3
    assert isinstance(payloads[0]["flag"], bool)


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize(
    "strategy", ["unknown", "text", "text::too_short", path("text"), None, 42, []]
)
def test_rejected_strategies(selection_model, api, strategy):
    with pytest.raises(GenerationError) as error:
        api(selection_model, valid=False, strategy=strategy)
    assert error.value.context["code"] == "unsupported_strategy"


@pytest.mark.parametrize("strategy", ["all", "all_violations"])
def test_case_rejects_enumeration(selection_model, strategy):
    with pytest.raises(GenerationError) as error:
        case(selection_model, valid=False, strategy=strategy)
    assert error.value.context["code"] == "unsupported_strategy"


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("violation", [V.TYPE_MISMATCH, V.MISSING_FIELD])
def test_explicit_capability_without_flag(selection_model, api, violation):
    result = api(
        selection_model, valid=False, target=path("flag").violate(violation), seed=0
    )
    payload = result[0] if api is cases else result
    assert len(payload["text"]) >= 3
    if violation == V.MISSING_FIELD:
        assert "flag" not in payload
    else:
        assert not isinstance(payload["flag"], bool)
    # The explicit request does not change future automatic eligibility.
    automatic = case(selection_model, valid=False, seed=0)
    assert len(automatic["text"]) < 3
    assert isinstance(automatic["flag"], bool)


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize(
    "selector,code",
    [
        (path("missing"), "field_not_found"),
        (path("flag"), "no_constraints_field"),
        (path("text").violate(V.BELOW_MIN), "invalid_forced_violation"),
        (path("optional").violate(V.MISSING_FIELD), "no_constraints_field"),
    ],
)
def test_target_planning_errors(selection_model, api, selector, code):
    with pytest.raises(PlanningError) as error:
        api(selection_model, valid=False, target=selector)
    assert error.value.context["code"] == code


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize(
    "kwargs,code",
    [
        ({"target": "text", "valid": False}, "invalid_target"),
        ({"target": path("text")}, "invalid_target_for_valid"),
        ({"strategy": "random"}, "invalid_strategy_for_valid"),
        (
            {"valid": False, "strategy": "random", "target": path("text")},
            "invalid_strategy_for_target",
        ),
        ({"allow_type_mismatch": True}, "invalid_flag_for_valid"),
    ],
)
def test_invalid_combinations(selection_model, api, kwargs, code):
    with pytest.raises(GenerationError) as error:
        api(selection_model, **kwargs)
    assert error.value.context["code"] == code


@pytest.mark.parametrize("count", [0, 2, 5])
def test_target_rejects_batch_count(selection_model, count):
    with pytest.raises(GenerationError) as error:
        cases(selection_model, valid=False, target=path("text"), count=count)
    assert error.value.context["code"] == (
        "invalid_count" if count == 0 else "invalid_count_for_target"
    )


@pytest.mark.parametrize("strategy", ["all", "all_violations"])
def test_enumeration_ignores_positive_count(selection_model, strategy):
    assert cases(
        selection_model, valid=False, strategy=strategy, count=100, seed=0
    ) == (cases(selection_model, valid=False, strategy=strategy, count=1, seed=0))


@pytest.mark.parametrize("api", [case, cases])
def test_typed_and_string_targets_with_overrides(selection_model, api):
    kwargs = {
        "valid": False,
        "seed": 0,
        "overrides": [path("text").set("override"), path("flag").set(True)],
    }
    result = api(
        selection_model, target=path(selection_model, lambda m: m.text), **kwargs
    )
    assert result == api(selection_model, target=path("text"), **kwargs)
    payload = result[0] if api is cases else result
    assert len(payload["text"]) < 3
    assert payload["flag"] is True


@pytest.mark.parametrize("name", ["first", "random", "all", "all_violations"])
def test_targets_named_like_strategies_are_fields(name):
    model = make_dataclass("Names", [(name, Annotated[str, MinLength(3)])])
    payload = case(model, valid=False, target=path(name), seed=0)
    assert len(payload[name]) < 3


def test_nested_object_cannot_be_type_mismatch_target():
    @dataclass
    class Child:
        flag: bool

    @dataclass
    class Parent:
        child: Child

    with pytest.raises(PlanningError) as error:
        case(Parent, valid=False, target=path("child").violate(V.TYPE_MISMATCH))
    assert error.value.context["code"] == "no_constraints_field"
    payload = case(
        Parent,
        valid=False,
        target=path(Parent, lambda m: m.child.flag).violate(V.TYPE_MISMATCH),
    )
    assert not isinstance(payload["child"]["flag"], bool)


def test_valid_tracing_remains_unavailable(selection_model):
    with pytest.raises(GenerationError) as error:
        case(selection_model, tracer=Tracer())
    assert error.value.context["code"] == "tracing_for_valid"


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("violation", [V.TYPE_MISMATCH, V.MISSING_FIELD])
def test_explicit_violation_when_no_automatic_candidates(api, violation):
    model = make_dataclass("Unconstrained", [("flag", bool)])
    with pytest.raises(PlanningError) as error:
        api(model, valid=False)
    assert error.value.context["code"] == "no_violation_candidate"
    result = api(model, valid=False, target=path("flag").violate(violation))
    payload = result[0] if api is cases else result
    if violation == V.MISSING_FIELD:
        assert payload == {}
    else:
        assert not isinstance(payload["flag"], bool)


@pytest.mark.parametrize("strategy", ["random", "all", "all_violations"])
def test_cases_target_disallows_every_nondefault_strategy(selection_model, strategy):
    with pytest.raises(GenerationError) as error:
        cases(selection_model, valid=False, strategy=strategy, target=path("text"))
    assert error.value.context["code"] == "invalid_strategy_for_target"


@pytest.mark.parametrize("strategy", ["first", "random"])
@pytest.mark.parametrize("seed", [0, 7, -1])
def test_automatic_batch_order_and_count(selection_model, strategy, seed):
    names = ["text", "flag", "optional"]
    expected = names[:2] if strategy == "first" else Random(seed).sample(names, k=2)
    payloads = cases(
        selection_model,
        valid=False,
        strategy=strategy,
        count=2,
        seed=seed,
        allow_type_mismatch=True,
    )
    selected = []
    for payload in payloads:
        mismatched = [
            name
            for name in names
            if not isinstance(payload[name], str if name == "text" else bool)
        ]
        assert len(mismatched) == 1
        selected.extend(mismatched)
    assert selected == expected
    with pytest.raises(PlanningError) as error:
        cases(
            selection_model,
            valid=False,
            strategy=strategy,
            count=4,
            allow_type_mismatch=True,
        )
    assert error.value.context["code"] == "too_many_requested"
