from datetime import date, datetime, time, timedelta

import pytest

from conformly import GreaterOrEqual, LessOrEqual
from conformly._internal.generator.context import create_context
from conformly._internal.generator.types.temporal import generate_value
from conformly._internal.resolver.semantics.temporal import create_temporal_semantic
from conformly._internal.types import FieldKind


@pytest.mark.parametrize(
    "kind,runtime_type",
    [
        (FieldKind.DATE, date),
        (FieldKind.DATETIME, datetime),
        (FieldKind.TIME, time),
        (FieldKind.TIMEDELTA, timedelta),
    ],
)
@pytest.mark.parametrize("endpoint", ["min", "max"])
def test_exact_domain_endpoints(kind, runtime_type, endpoint):
    value = getattr(runtime_type, endpoint)
    semantic = create_temporal_semantic(
        kind, (GreaterOrEqual(value), LessOrEqual(value))
    )
    assert generate_value(create_context(0), semantic, None) == value


@pytest.mark.parametrize("seed", [0, -1, 1])
def test_seed_reproducibility(seed):
    semantic = create_temporal_semantic(FieldKind.DATETIME, ())
    assert generate_value(create_context(seed), semantic, None) == generate_value(
        create_context(seed), semantic, None
    )
