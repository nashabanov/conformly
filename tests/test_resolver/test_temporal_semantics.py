from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest

from conformly import GreaterOrEqual, GreaterThan, LessOrEqual, LessThan, MultipleOf
from conformly._internal.resolver.semantics._domains import finite_cardinality
from conformly._internal.resolver.semantics.temporal import create_temporal_semantic
from conformly._internal.types import FieldKind
from conformly.exceptions import SchemaError


@pytest.mark.parametrize(
    "kind,value",
    [
        (FieldKind.DATE, date(2024, 2, 29)),
        (FieldKind.DATETIME, datetime(2024, 2, 29)),
        (FieldKind.TIME, time(12)),
        (FieldKind.TIMEDELTA, timedelta(days=-1)),
    ],
)
def test_intersection_has_exact_cardinality(kind, value):
    semantic = create_temporal_semantic(
        kind, (GreaterOrEqual(value), LessOrEqual(value))
    )
    assert finite_cardinality(semantic) == 1
    assert semantic.has_constraints
    with pytest.raises(SchemaError):
        create_temporal_semantic(kind, (GreaterThan(value), LessThan(value)))
    with pytest.raises(SchemaError):
        create_temporal_semantic(kind, (MultipleOf(2),))


def test_aware_datetime_outside_utc_domain_rejected():
    value = datetime.min.replace(tzinfo=timezone(timedelta(hours=1)))
    with pytest.raises(SchemaError, match="representable"):
        create_temporal_semantic(FieldKind.DATETIME, (GreaterThan(value),))


def test_aware_datetime_same_instant_with_different_offsets():
    low = datetime(2024, 1, 1, tzinfo=UTC)
    high = low.astimezone(timezone(timedelta(hours=-5)))
    semantic = create_temporal_semantic(
        FieldKind.DATETIME, (GreaterOrEqual(low), LessOrEqual(high))
    )
    assert semantic.aware
    assert finite_cardinality(semantic) == 1
