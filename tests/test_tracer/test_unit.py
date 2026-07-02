from conformly._internal.tracer import Trace, Tracer, ValueSource
from conformly._internal.types import ViolationType


def test_build_returns_trace_with_recorded_data() -> None:
    tracer = Tracer()

    tracer.set_target_path("profile.email")
    tracer.set_violation(ViolationType.PATTERN_MISMATCH)
    tracer.set_seed(123)
    tracer.set_generated_value("invalid-email")
    tracer.set_value_source(ValueSource.GENERATED)

    trace = tracer.build()

    assert trace == Trace(
        target_path="profile.email",
        seed=123,
        violation=ViolationType.PATTERN_MISMATCH,
        generated_value="invalid-email",
        value_source=ValueSource.GENERATED,
    )


def test_build_supports_optional_plan_fields() -> None:
    tracer = Tracer()

    tracer.set_target_path("name")
    tracer.set_generated_value("John")
    tracer.set_value_source(ValueSource.MODEL_DEFAULT)

    trace = tracer.build()

    assert trace == Trace(
        target_path="name",
        seed=None,
        violation=None,
        generated_value="John",
        value_source=ValueSource.MODEL_DEFAULT,
    )
