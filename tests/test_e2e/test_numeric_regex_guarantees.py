from dataclasses import make_dataclass
from decimal import Decimal
import math
import re
from typing import Annotated

import pytest

from conformly import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    MultipleOf,
    Pattern,
    V,
    case,
    cases,
    path,
)
from conformly.exceptions import GenerationError, PlanningError, SchemaError


def model_for(annotation):
    return make_dataclass("NumericRegexModel", [("value", annotation), ("other", int)])


@pytest.mark.parametrize("divisor", [1, 1.0, 0.5])
def test_impossible_integer_not_multiple_is_not_planned(divisor):
    model = model_for(Annotated[int, MultipleOf(divisor), GreaterOrEqual(0)])
    with pytest.raises(PlanningError) as exc:
        case(model, valid=False, target=path("value").violate(V.NOT_MULTIPLE))
    assert exc.value.context["code"] == "invalid_forced_violation"
    payloads = cases(model, valid=False, strategy="all_violations")
    assert len(payloads) == 1
    assert payloads[0]["value"] < 0


@pytest.mark.parametrize("divisor", [2, 3, 1.5])
def test_integer_not_multiple_actually_breaks_divisibility(divisor):
    model = model_for(Annotated[int, MultipleOf(divisor)])
    for seed in range(20):
        value = case(
            model,
            valid=False,
            seed=seed,
            target=path("value").violate(V.NOT_MULTIPLE),
        )["value"]
        assert Decimal(value) % Decimal(str(divisor)) != 0


@pytest.mark.parametrize(
    "kind,low,high,divisor",
    [
        (int, -20, -10, 3),
        (int, 10, 20, 3),
        (int, -7, -2, 1.5),
        (float, 0.3, 0.3, 0.1),
        (float, -0.9, -0.3, 0.1),
        (float, 0.1, 0.9, 0.25),
        (float, -20, -10, 2.5),
    ],
)
def test_valid_bounds_and_multiples(kind, low, high, divisor):
    model = model_for(
        Annotated[kind, GreaterOrEqual(low), LessOrEqual(high), MultipleOf(divisor)]
    )
    for seed in range(30):
        value = case(model, seed=seed)["value"]
        assert low <= value <= high
        quotient = Decimal(str(value)) / Decimal(str(divisor))
        assert abs(quotient - quotient.to_integral_value()) <= Decimal("1e-9")


@pytest.mark.parametrize(
    "kind,low,high,divisor",
    [
        (int, 4, 5, 3),
        (int, -5, -4, 3),
        (float, 0.31, 0.39, 0.1),
        (float, -0.39, -0.31, 0.1),
    ],
)
def test_range_without_multiples_fails(kind, low, high, divisor):
    model = model_for(
        Annotated[kind, GreaterOrEqual(low), LessOrEqual(high), MultipleOf(divisor)]
    )
    with pytest.raises(GenerationError) as exc:
        case(model)
    assert exc.value.context["code"] == "no_multiples_of"


@pytest.mark.parametrize("kind", [int, float])
@pytest.mark.parametrize(
    "lower,upper",
    [
        (GreaterThan(-1.5), LessThan(1.5)),
        (GreaterOrEqual(-1.5), LessOrEqual(1.5)),
        (GreaterThan(0.3), LessThan(0.3000000000000001)),
    ],
)
def test_open_closed_and_narrow_bounds(kind, lower, upper):
    model = model_for(Annotated[kind, lower, upper])
    if kind is int and lower.value == 0.3:
        with pytest.raises(SchemaError):
            case(model)
        return
    for seed in range(20):
        value = case(model, seed=seed)["value"]
        assert (
            value > lower.value
            if isinstance(lower, GreaterThan)
            else value >= lower.value
        )
        assert (
            value < upper.value if isinstance(upper, LessThan) else value <= upper.value
        )


@pytest.mark.parametrize("divisor", [0.1, 0.25, 3, 1e-300])
def test_float_not_multiple_is_verified_even_in_singleton_range(divisor):
    model = model_for(
        Annotated[float, GreaterOrEqual(0), LessOrEqual(0), MultipleOf(divisor)]
    )
    for seed in range(20):
        value = case(
            model,
            valid=False,
            seed=seed,
            target=path("value").violate(V.NOT_MULTIPLE),
        )["value"]
        quotient = value / divisor
        assert not math.isclose(quotient, round(quotient), rel_tol=0, abs_tol=1e-9)


@pytest.mark.parametrize("pattern", ["", ".*", "(?s).*", "(?s)^.*$"])
def test_obvious_universal_patterns_are_not_planned(pattern):
    model = model_for(Annotated[str, Pattern(pattern), MinLength(1)])
    with pytest.raises(PlanningError):
        case(model, valid=False, target=path("value").violate(V.PATTERN_MISMATCH))
    assert len(cases(model, valid=False, strategy="all_violations")) == 1


@pytest.mark.parametrize("pattern", ["^a*$", "[a-z]{3}", "a", "^$"])
def test_regex_mismatch_has_no_search_match(pattern):
    model = model_for(Annotated[str, Pattern(pattern)])
    value = case(model, valid=False, target=path("value").violate(V.PATTERN_MISMATCH))[
        "value"
    ]
    assert re.search(pattern, value) is None


@pytest.mark.parametrize("pattern", ["a*", r"(?s)^.+$|^$"])
def test_unrecognized_universal_pattern_exhausts_with_structured_error(pattern):
    model = model_for(Annotated[str, Pattern(pattern)])
    with pytest.raises(GenerationError) as exc:
        case(model, valid=False, target=path("value").violate(V.PATTERN_MISMATCH))
    assert exc.value.context["code"] == "pattern_inversion_exhausted"
    assert exc.value.context["attempts"] > 0


def test_incompatible_pattern_length_never_returns_valid_data():
    model = model_for(Annotated[str, Pattern("^a{3}$"), MaxLength(2)])
    with pytest.raises(GenerationError) as exc:
        case(model, valid=True)
    assert exc.value.context["code"] == "pattern_generation_timeout"


@pytest.mark.parametrize("divisor", [0, -1, math.inf, math.nan])
def test_invalid_divisor_is_a_schema_error(divisor):
    with pytest.raises(SchemaError) as exc:
        case(model_for(Annotated[float, MultipleOf(divisor)]))
    assert exc.value.context["code"] == "invalid_multiple_of"
