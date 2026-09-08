from dataclasses import dataclass

import pytest

from conformly import Email, V, case, path
from conformly._internal.tracer import ValueSource
from conformly.exceptions import ConformlyError
from conformly.tracer import Tracer


@dataclass
class User:
    email: Email


def test_tracer_with_valid_true_fails() -> None:
    tracer = Tracer()

    with pytest.raises(ConformlyError):
        case(User, tracer=tracer)


def test_tracer_happy_path() -> None:
    tracer = Tracer()

    case(
        User,
        valid=False,
        seed=123,
        strategy=path(User, lambda u: u.email).violate(V.WRONG_EMAIL_FORMAT),
        tracer=tracer,
    )

    trace = tracer.build()

    assert trace.target_path == "email"
    assert trace.seed == 123
    assert trace.violation == V.WRONG_EMAIL_FORMAT
    assert trace.generated_value is not None
    assert trace.value_source == ValueSource.GENERATED


@pytest.mark.parametrize("seed", [0, 1, -1])
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(
    ("selection", "target"),
    [
        (selection, target)
        for selection in ("dsl", "string", "plain")
        for target in ("before", "middle", "after")
    ]
    + [("first", "before"), ("random", "before")],
)
def test_trace_describes_selected_target(seed, target, nested, selection):
    from dataclasses import field
    from typing import Annotated
    from uuid import UUID

    from conformly import GreaterOrEqual

    @dataclass
    class Fields:
        before: Annotated[int, GreaterOrEqual(10)] = 20
        middle: Annotated[int, GreaterOrEqual(10)] = 30
        after: Annotated[int, GreaterOrEqual(10)] = 40
        items: list[int] = field(default_factory=lambda: [1, 2])
        pair: tuple[int, int] = (1, 2)

    @dataclass
    class Root:
        identifier: UUID
        fields: Fields
        tail: str = "default"

    model = Root if nested else Fields
    target_path = f"fields.{target}" if nested else target
    strategies = {
        "dsl": path(target_path).violate(V.BELOW_MIN),
        "string": f"{target_path}::below_min",
        "plain": target_path,
        "first": "first",
        "random": "random",
    }
    strategy = strategies[selection]
    tracer = Tracer()
    # Reuse must replace every piece of stale metadata.
    tracer.set_target_path("stale")
    tracer.set_violation(V.EXTRA_FIELD)
    tracer.set_value_source(ValueSource.OVERRIDDEN)
    tracer.set_generated_value("stale")
    payload = case(model, valid=False, seed=seed, strategy=strategy, tracer=tracer)
    assert payload == case(model, valid=False, seed=seed, strategy=strategy)
    trace = tracer.build()
    if selection not in ("first", "random"):
        assert trace.target_path == target_path
    elif selection == "first":
        assert trace.target_path == ("identifier" if nested else "before")
    container = payload
    for name in trace.target_path.split("."):
        container = container[name]
    assert trace.generated_value == container
    assert trace.seed == seed
    assert trace.value_source == ValueSource.GENERATED
    if trace.target_path == "identifier":
        assert trace.violation == V.WRONG_UUID_FORMAT
    else:
        assert trace.violation == V.BELOW_MIN
        assert container < 10


def test_trace_missing_field_preserves_target_metadata():
    from typing import Annotated

    from conformly import GreaterOrEqual
    from conformly._internal.types import UNSET

    @dataclass
    class Fields:
        target: Annotated[int, GreaterOrEqual(10)]
        after: str = "default"

    tracer = Tracer()
    payload = case(
        Fields,
        valid=False,
        seed=0,
        strategy=path("target").violate(V.MISSING_FIELD),
        tracer=tracer,
        overrides=[path("target").set(50), path("after").set("override")],
    )
    assert payload == {"after": "override"}
    trace = tracer.build()
    assert trace.target_path == "target"
    assert trace.violation == V.MISSING_FIELD
    assert trace.generated_value is UNSET
    assert trace.value_source == ValueSource.GENERATED


def test_tracing_does_not_change_factory_calls_or_payload():
    from dataclasses import field
    from typing import Annotated

    from conformly import GreaterOrEqual

    calls = []

    def factory():
        calls.append(len(calls) + 1)
        return [calls[-1]]

    @dataclass
    class Fields:
        before: list[int] = field(default_factory=factory)
        target: Annotated[int, GreaterOrEqual(10)] = 20
        after: list[int] = field(default_factory=factory)
        tail: str = "default"

    plain = case(Fields, valid=False, seed=0, strategy="target")
    assert calls == [1, 2]
    calls.clear()
    tracer = Tracer()
    traced = case(Fields, valid=False, seed=0, strategy="target", tracer=tracer)
    assert calls == [1, 2]
    assert traced == plain
    assert traced["before"] == [1]
    assert traced["after"] == [2]
    assert tracer.build().generated_value == traced["target"]
