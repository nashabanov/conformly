from dataclasses import dataclass, field
from typing import Annotated
from uuid import UUID

import pytest

from conformly import GreaterOrEqual, Pattern, V, case, cases, path
from conformly.tracer import Tracer


@dataclass
class Fields:
    before: Annotated[int, GreaterOrEqual(10)]
    middle: Annotated[int, GreaterOrEqual(10)]
    after: Annotated[int, GreaterOrEqual(10)]


@dataclass
class NestedFields:
    before: Fields
    middle: Fields
    after: Fields


@dataclass
class RandomFields:
    number: int
    token: Annotated[str, Pattern(r"[a-z]{8}[0-9]{4}")]
    identifier: UUID
    nested: NestedFields


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("model", [Fields, NestedFields, RandomFields])
@pytest.mark.parametrize("seed", [0, 1, -1])
@pytest.mark.parametrize("valid", [True, False])
def test_seed_reproduces_payload(api, model, seed, valid):
    kwargs = {"valid": valid, "seed": seed}
    if not valid:
        kwargs["strategy"] = "random"
    if api is cases:
        kwargs["count"] = 3
    assert api(model, **kwargs) == api(model, **kwargs)


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("target", ["before", "middle", "after"])
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("violation", [V.BELOW_MIN, V.MISSING_FIELD])
def test_invalid_generation_preserves_unrelated_overrides(
    api, target, nested, violation
):
    model = NestedFields if nested else Fields
    names = ["before", "middle", "after"]
    paths = (
        [f"{parent}.{name}" for parent in names for name in names] if nested else names
    )
    target_path = f"middle.{target}" if nested else target
    overrides = [path(name).set(100 + i) for i, name in enumerate(paths)]
    result = api(
        model,
        valid=False,
        seed=0,
        strategy=path(target_path).violate(violation),
        overrides=overrides,
    )
    payload = result[0] if api is cases else result
    for i, name in enumerate(paths):
        *parents, leaf = name.split(".")
        container = payload
        for parent in parents:
            container = container[parent]
        if name != target_path:
            assert container[leaf] == 100 + i
        elif violation == V.MISSING_FIELD:
            assert leaf not in container
        else:
            assert container[leaf] < 10


def test_extra_fields_preserve_overrides_at_every_depth():
    names = ["before", "middle", "after"]
    overrides = [
        path(f"{parent}.{name}").set(123) for parent in names for name in names
    ]
    payloads = cases(
        NestedFields,
        valid=False,
        seed=0,
        strategy="all_violations",
        allow_structural_violations=True,
        overrides=overrides,
    )
    extra_payloads = [
        payload
        for payload in payloads
        if "extra" in payload
        or any(
            isinstance(value, dict) and "extra" in value for value in payload.values()
        )
    ]
    assert len(extra_payloads) == 4
    for payload in extra_payloads:
        for parent in names:
            for name in names:
                assert payload[parent][name] == 123


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("seed", [0, 1, -1])
@pytest.mark.parametrize("violation", [V.WRONG_UUID_FORMAT, V.WRONG_UUID_CHARACTER])
def test_uuid_invalid_generation_is_seeded(api, seed, violation):
    strategy = path("identifier").violate(violation)
    assert api(RandomFields, valid=False, seed=seed, strategy=strategy) == api(
        RandomFields, valid=False, seed=seed, strategy=strategy
    )


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("valid", [True, False])
def test_default_factories_run_once_per_generated_field(api, valid):
    calls = []

    def factory():
        calls.append(len(calls) + 1)
        return [calls[-1]]

    @dataclass
    class Defaults:
        before: list[int] = field(default_factory=factory)
        target: Annotated[int, GreaterOrEqual(10)] = 20
        after: list[int] = field(default_factory=factory)

    kwargs = {"valid": valid, "seed": 0}
    if api is cases:
        if valid:
            kwargs["count"] = 2
        else:
            kwargs.update(strategy="all_violations", allow_structural_violations=True)
    elif not valid:
        kwargs.update(strategy="target", tracer=Tracer())
    result = api(Defaults, **kwargs)
    payloads = result if api is cases else [result]
    factory_values = [
        payload[name]
        for payload in payloads
        for name in ("before", "after")
        if name in payload
    ]
    assert calls == list(range(1, len(factory_values) + 1))
    assert factory_values == [[number] for number in calls]


def test_extra_field_does_not_replace_existing_field_overrides():
    @dataclass
    class ExistingExtra:
        extra: int
        extra_1: int

    payloads = cases(
        ExistingExtra,
        valid=False,
        seed=0,
        strategy="all_violations",
        allow_structural_violations=True,
        overrides=[path("extra").set(111), path("extra_1").set(222)],
    )
    extra_payloads = [payload for payload in payloads if len(payload) == 3]
    assert len(extra_payloads) == 1
    assert extra_payloads[0]["extra"] == 111
    assert extra_payloads[0]["extra_1"] == 222
    assert isinstance(extra_payloads[0]["extra_2"], str)
