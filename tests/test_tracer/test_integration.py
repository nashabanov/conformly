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
