from datetime import UTC, date, datetime, time, timedelta

from .._errors import generation_error
from ..context import GenerationContext

from conformly._internal.resolver.semantics import TemporalSemantic
from conformly._internal.resolver.semantics.temporal import MICROSECONDS_PER_DAY
from conformly._internal.types import FieldKind, ViolationType


def generate_value(
    ctx: GenerationContext, semantic: TemporalSemantic, violation: ViolationType | None
) -> date | time | timedelta:
    if violation is None:
        tick = ctx.rng.randint(semantic.min_value, semantic.max_value)
    elif (
        violation == ViolationType.BELOW_MIN
        and semantic.min_value > semantic.domain_min
    ):
        tick = semantic.min_value - 1
    elif (
        violation == ViolationType.ABOVE_MAX
        and semantic.max_value < semantic.domain_max
    ):
        tick = semantic.max_value + 1
    else:
        raise generation_error(
            "No representable temporal violation available",
            code="unsupported_temporal_violation",
            violation=violation.value,
        )

    match semantic.kind:
        case FieldKind.DATE:
            return date.fromordinal(tick)
        case FieldKind.TIME:
            return _time_from_tick(tick)
        case FieldKind.DATETIME:
            day, remainder = divmod(tick, MICROSECONDS_PER_DAY)
            return datetime.combine(
                date.fromordinal(day + 1),
                _time_from_tick(remainder),
                tzinfo=UTC if semantic.aware else None,
            )
        case FieldKind.TIMEDELTA:
            return timedelta(microseconds=tick)
        case _:
            raise generation_error(
                "Unsupported temporal kind",
                code="unsupported_temporal_kind",
                kind=semantic.kind.value,
            )


def _time_from_tick(tick: int) -> time:
    seconds, microsecond = divmod(tick, 1_000_000)
    hour, seconds = divmod(seconds, 3600)
    minute, second = divmod(seconds, 60)
    return time(hour, minute, second, microsecond)
