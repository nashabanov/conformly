from dataclasses import make_dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Annotated, TypedDict

import pytest

from conformly import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    V,
    case,
    cases,
    path,
)
from conformly.exceptions import PlanningError, SchemaError

BOUNDS = [
    (date, date(2024, 2, 28), date(2024, 3, 1), timedelta(days=1)),
    (datetime, datetime(2024, 2, 29), datetime(2024, 3, 1), timedelta(microseconds=1)),
    (time, time(12), time(13), timedelta(microseconds=1)),
    (timedelta, timedelta(days=-1), timedelta(days=1), timedelta(microseconds=1)),
]


def model_for(kind, *constraints):
    return make_dataclass("TemporalModel", [("value", Annotated[kind, *constraints])])


@pytest.mark.parametrize("kind,low,high,step", BOUNDS)
@pytest.mark.parametrize("lower", [GreaterThan, GreaterOrEqual])
@pytest.mark.parametrize("upper", [LessThan, LessOrEqual])
def test_bounds_and_minimal_violations(kind, low, high, step, lower, upper):
    model = model_for(kind, lower(low), upper(high))
    for seed in (0, -1, 1, 42):
        value = case(model, seed=seed)["value"]
        assert type(value) is kind
        assert (value > low) if lower is GreaterThan else (value >= low)
        assert (value < high) if upper is LessThan else (value <= high)
        assert case(model, seed=seed) == case(model, seed=seed)
    below = case(model, valid=False, strategy=path("value").violate(V.BELOW_MIN))
    above = case(model, valid=False, strategy=path("value").violate(V.ABOVE_MAX))
    assert below["value"] <= low if lower is GreaterThan else below["value"] < low
    assert above["value"] >= high if upper is LessThan else above["value"] > high
    if kind is not time:
        assert below["value"] == (low if lower is GreaterThan else low - step)
        assert above["value"] == (high if upper is LessThan else high + step)


@pytest.mark.parametrize("kind,low,high,step", BOUNDS)
def test_singleton_and_empty_bounds(kind, low, high, step):
    model = model_for(kind, GreaterOrEqual(low), LessOrEqual(low))
    assert case(model)["value"] == low
    with pytest.raises(SchemaError):
        case(model_for(kind, GreaterThan(low), LessOrEqual(low)))
    with pytest.raises(SchemaError):
        case(model_for(kind, GreaterOrEqual(high), LessThan(low)))


@pytest.mark.parametrize("kind", [date, datetime, time, timedelta])
def test_unconstrained_and_type_structural_violations(kind):
    model = make_dataclass("TemporalModel", [("value", kind), ("other", kind)])
    assert type(case(model)["value"]) is kind
    invalid = case(
        model,
        valid=False,
        strategy=path("value").violate(V.TYPE_MISMATCH),
        allow_type_mismatch=True,
    )
    assert not isinstance(invalid["value"], kind)
    assert type(invalid["other"]) is kind
    missing = cases(
        model,
        valid=False,
        strategy="all",
        allow_structural_violations=True,
    )[0]
    assert "value" not in missing
    assert type(missing["other"]) is kind
    with pytest.raises(PlanningError):
        case(model, valid=False, strategy=path("value").violate(V.BELOW_MIN))


@pytest.mark.parametrize("kind", [date, datetime, time, timedelta])
@pytest.mark.parametrize(
    "bound,violation", [("min", V.BELOW_MIN), ("max", V.ABOVE_MAX)]
)
def test_domain_boundaries_have_no_violation(kind, bound, violation):
    limit = getattr(kind, bound)
    constraint = GreaterOrEqual(limit) if bound == "min" else LessOrEqual(limit)
    assert type(case(model_for(kind, constraint))["value"]) is kind
    with pytest.raises(PlanningError):
        case(
            model_for(kind, constraint),
            valid=False,
            strategy=path("value").violate(violation),
        )
    exclusive = GreaterThan(limit) if bound == "max" else LessThan(limit)
    with pytest.raises(SchemaError):
        case(model_for(kind, exclusive))


def test_aware_datetime_bounds_normalize_to_utc():
    low = datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=3)))
    high = datetime(2024, 1, 2, tzinfo=UTC)
    model = model_for(datetime, GreaterThan(low), LessThan(high))
    value = case(model, seed=0)["value"]
    assert value.tzinfo is UTC
    assert low < value < high
    for violation in (V.BELOW_MIN, V.ABOVE_MAX):
        invalid = case(model, valid=False, strategy=path("value").violate(violation))[
            "value"
        ]
        assert invalid == (low if violation == V.BELOW_MIN else high)


@pytest.mark.parametrize(
    "kind, constraints",
    [
        (date, [GreaterThan(datetime(2024, 1, 1))]),
        (datetime, [GreaterThan(date(2024, 1, 1))]),
        (timedelta, [LessThan(10)]),
        (time, [GreaterThan(time(12, tzinfo=UTC))]),
        (
            datetime,
            [
                GreaterThan(datetime(2024, 1, 1)),
                LessThan(datetime(2025, 1, 1, tzinfo=UTC)),
            ],
        ),
    ],
)
def test_incompatible_bounds_rejected(kind, constraints):
    with pytest.raises(SchemaError):
        case(model_for(kind, *constraints))


def test_typeddict_collections_and_optional_temporal_fields():
    class Payload(TypedDict):
        dates: list[Annotated[date, GreaterOrEqual(date(2024, 1, 1))]]
        times: tuple[time, timedelta]
        timestamps: dict[str, datetime]
        optional: date | None

    payload = case(Payload, seed=0)
    assert all(type(v) is date and v >= date(2024, 1, 1) for v in payload["dates"])
    assert type(payload["times"][0]) is time
    assert type(payload["times"][1]) is timedelta
    assert all(type(v) is datetime for v in payload["timestamps"].values())
    assert payload["optional"] is None or type(payload["optional"]) is date


def test_pydantic_field_bounds():
    pydantic = pytest.importorskip("pydantic")

    class Model(pydantic.BaseModel):
        day: date = pydantic.Field(gt=date(2024, 1, 1), le=date(2024, 12, 31))
        moment: datetime = pydantic.Field(
            ge=datetime(2024, 1, 1), lt=datetime(2025, 1, 1)
        )
        clock: time = pydantic.Field(ge=time(9), le=time(17))
        duration: timedelta = pydantic.Field(gt=timedelta(0), lt=timedelta(days=1))

    pydantic_model = Model.model_validate(case(Model, seed=0))
    assert pydantic_model.day.year == 2024
    for name in ("day", "moment", "clock", "duration"):
        for violation in (V.BELOW_MIN, V.ABOVE_MAX):
            with pytest.raises(pydantic.ValidationError):
                Model.model_validate(
                    case(Model, valid=False, strategy=path(name).violate(violation))
                )


@pytest.mark.parametrize("kind,low,high,step", BOUNDS)
def test_attrs_temporal_bounds(kind, low, high, step):
    attrs = pytest.importorskip("attrs")
    model = attrs.make_class(
        "TemporalAttrs",
        {"value": attrs.field(type=Annotated[kind, GreaterThan(low), LessThan(high)])},
    )
    value = case(model, seed=0)["value"]
    assert type(value) is kind
    assert low < value < high


@pytest.mark.parametrize("collection", [list, set, frozenset])
def test_unique_date_collections_reject_impossible_size(collection):
    from conformly import MinItems, UniqueItems
    from conformly.exceptions import GenerationError

    item = Annotated[
        date, GreaterOrEqual(date(2024, 2, 29)), LessOrEqual(date(2024, 2, 29))
    ]
    model = model_for(collection[item], MinItems(2), UniqueItems(True))
    with pytest.raises(GenerationError):
        case(model)


def test_nested_temporal_target_preserves_other_fields():
    child = model_for(date, GreaterOrEqual(date(2024, 1, 1)))
    parent = make_dataclass("Parent", [("left", child), ("right", child)])
    payload = case(
        parent, valid=False, strategy=path("left.value").violate(V.BELOW_MIN)
    )
    assert payload["left"]["value"] == date(2023, 12, 31)
    assert payload["right"]["value"] >= date(2024, 1, 1)
