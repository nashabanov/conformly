from conformly._internal.tracer import Trace, Tracer, ValueSource
from conformly._internal.types import ViolationType


def test_build_returns_trace_with_recorded_data() -> None:
    tracer = Tracer()

    tracer.record_plan(
        target_path="profile.email",
        constraint="pattern",
        violation=ViolationType.PATTERN_MISMATCH,
    )
    tracer.record_generation(
        seed=123,
        value="invalid-email",
        source=ValueSource.GENERATED,
    )

    trace = tracer.build()

    assert trace == Trace(
        target_path="profile.email",
        seed=123,
        constraint="pattern",
        violation=ViolationType.PATTERN_MISMATCH,
        generated_value="invalid-email",
        value_source=ValueSource.GENERATED,
    )


def test_build_supports_optional_plan_fields() -> None:
    tracer = Tracer()

    tracer.record_plan(target_path="name")
    tracer.record_generation(
        seed=None,
        value="John",
        source=ValueSource.MODEL_DEFAULT,
    )

    trace = tracer.build()

    assert trace == Trace(
        target_path="name",
        seed=None,
        constraint=None,
        violation=None,
        generated_value="John",
        value_source=ValueSource.MODEL_DEFAULT,
    )
