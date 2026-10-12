from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from .base import BaseSemantic

from conformly._internal.constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
)
from conformly._internal.types import FieldKind
from conformly.exceptions import SchemaError

MICROSECONDS_PER_DAY = 86_400_000_000
TEMPORAL_TYPES = {
    FieldKind.DATE: date,
    FieldKind.DATETIME: datetime,
    FieldKind.TIME: time,
    FieldKind.TIMEDELTA: timedelta,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class TemporalSemantic(BaseSemantic):
    temporal_kind: FieldKind
    min_value: int
    max_value: int
    domain_min: int
    domain_max: int
    aware: bool = False

    @property
    def kind(self) -> FieldKind:
        return self.temporal_kind


def create_temporal_semantic(
    kind: FieldKind, constraints: tuple[Constraint, ...]
) -> TemporalSemantic:
    match kind:
        case FieldKind.DATE:
            domain_min, domain_max = 1, date.max.toordinal()
        case FieldKind.DATETIME:
            domain_min = 0
            domain_max = date.max.toordinal() * MICROSECONDS_PER_DAY - 1
        case FieldKind.TIME:
            domain_min, domain_max = 0, MICROSECONDS_PER_DAY - 1
        case FieldKind.TIMEDELTA:
            domain_min = timedelta.min.days * MICROSECONDS_PER_DAY
            domain_max = (timedelta.max.days + 1) * MICROSECONDS_PER_DAY - 1
        case _:
            raise ValueError(f"Unsupported temporal kind: {kind}")

    low, high = domain_min, domain_max
    awareness: bool | None = None
    for constraint in constraints:
        if not isinstance(
            constraint, (GreaterThan, GreaterOrEqual, LessThan, LessOrEqual)
        ):
            raise SchemaError(
                "Unsupported constraint for temporal type",
                context={"code": "unsupported_temporal_constraint", "kind": kind.value},
            )
        value = constraint.value
        # datetime subclasses date, but bounds must match the field exactly.
        if type(value) is not TEMPORAL_TYPES[kind]:
            raise SchemaError(
                "Temporal bound must match the field type",
                context={"code": "invalid_temporal_bound_type", "kind": kind.value},
            )
        if isinstance(value, (datetime, time)):
            aware = value.utcoffset() is not None
            if kind == FieldKind.TIME and aware:
                raise SchemaError(
                    "Aware time bounds are not supported",
                    context={"code": "aware_time_bounds"},
                )
            if awareness is not None and awareness != aware:
                raise SchemaError(
                    "Cannot mix aware and naive datetime bounds",
                    context={"code": "mixed_temporal_awareness"},
                )
            awareness = aware
        try:
            tick = temporal_tick(value)
        except (OverflowError, ValueError) as exc:
            raise SchemaError(
                "Temporal bound is outside the representable range",
                context={"code": "temporal_bound_overflow"},
            ) from exc
        match constraint:
            case GreaterThan():
                low = max(low, tick + 1)
            case GreaterOrEqual():
                low = max(low, tick)
            case LessThan():
                high = min(high, tick - 1)
            case LessOrEqual():
                high = min(high, tick)
    if low > high:
        raise SchemaError(
            "Temporal bounds contain no representable value",
            context={"code": "invalid_temporal_bounds", "min": low, "max": high},
        )
    return TemporalSemantic(
        temporal_kind=kind,
        min_value=low,
        max_value=high,
        domain_min=domain_min,
        domain_max=domain_max,
        aware=bool(awareness),
        has_constraints=bool(constraints),
    )


def temporal_tick(value: int | float | date | time | timedelta) -> int:
    if isinstance(value, datetime):
        if value.utcoffset() is not None:
            value = value.astimezone(UTC)
        return (value.toordinal() - 1) * MICROSECONDS_PER_DAY + _time_tick(value)
    if isinstance(value, date):
        return value.toordinal()
    if isinstance(value, time):
        return _time_tick(value)
    if isinstance(value, timedelta):
        return (
            value.days * MICROSECONDS_PER_DAY
            + value.seconds * 1_000_000
            + value.microseconds
        )
    raise ValueError("Expected temporal value")


def _time_tick(value: datetime | time) -> int:
    return (
        value.hour * 3600 + value.minute * 60 + value.second
    ) * 1_000_000 + value.microsecond
