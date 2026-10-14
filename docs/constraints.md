# Constraints

## Reference

Import constraints from `conformly` and attach them with `typing.Annotated`.
The table describes supported combinations; unrelated constraints on some types
are ignored rather than uniformly rejected. Do not depend on ignored metadata.

| Constraint | Field types | Meaning and small annotation example |
| --- | --- | --- |
| `MinLength(value: int)` | `str`, `bytes`, Email, URL types | Inclusive length minimum: `Annotated[str, MinLength(3)]` |
| `MaxLength(value: int)` | Same | Inclusive maximum: `Annotated[bytes, MaxLength(16)]` |
| `Pattern(regex: str)` | Plain `str` | Regex search: `Annotated[str, Pattern(r"^[A-Z]+$")]` |
| `GreaterThan(value)` | `int`, `float`, temporal types | Exclusive lower bound: `Annotated[int, GreaterThan(0)]` |
| `GreaterOrEqual(value)` | Same | Inclusive lower bound: `Annotated[int, GreaterOrEqual(18)]` |
| `LessThan(value)` | Same | Exclusive upper bound: `Annotated[float, LessThan(1.0)]` |
| `LessOrEqual(value)` | Same | Inclusive upper bound: `Annotated[int, LessOrEqual(120)]` |
| `MultipleOf(value: int | float)` | `int`, `float` | Multiple of a finite positive divisor: `Annotated[int, MultipleOf(5)]` |
| `OneOf(values: tuple)` | Closed sets represented by Enum/Literal | Allowed values; automatically extracted from `Literal["draft", "sent"]` |
| `MinItems(value: int)` | Lists, sets, frozensets, tuples, dicts | Minimum entry count: `Annotated[list[int], MinItems(1)]` |
| `MaxItems(value: int)` | Same | Maximum count: `Annotated[dict[str, int], MaxItems(5)]` |
| `UniqueItems(is_unique: bool)` | Lists; intrinsic for sets/frozensets | Structural uniqueness: `Annotated[list[int], UniqueItems(True)]` |

`OneOf` is exported, but attaching it to a plain `str` or `int` does not turn
that type into a closed set. Use `Literal` or Enum; their extracted `OneOf`
cannot be combined with further constraints, including another `OneOf`.
Dictionaries ignore `UniqueItems` because keys are already unique; tuples do
not implement this constraint.

## Declaration styles

Constraint objects work with all adapters:

```python
from dataclasses import dataclass, field
from typing import Annotated

from conformly import MinLength


@dataclass
class Product:
    name: Annotated[str, MinLength(3)]
    title: Annotated[str, "min_length=5", "max_length=200"]
    sku: str = field(metadata={"pattern": r"^[A-Z0-9]{8}$"})
```

Metadata keys are `gt`, `ge`, `lt`, `le`, `multiple_of`, `min_length`,
`max_length`, `pattern`, `min_items`, `max_items`, and `unique_items`.
`Annotated` also accepts dictionary metadata such as
`{"type": "min_length", "value": 3}`. Dataclass metadata uses the key/value
mapping above; keys beginning with `_` are ignored.
Pydantic extracts supported `Field()` metadata; see [integrations](integrations.md).

Prefer element annotations to distinguish element and collection constraints:

```python
from conformly import GreaterOrEqual, MaxItems, MinItems

prices: Annotated[
    list[Annotated[int, GreaterOrEqual(0)]], MinItems(1), MaxItems(5)
]
```

## Patterns and numeric bounds

`Pattern` uses Python regex search semantics, consistent with Pydantic: a match
anywhere in the string is sufficient. Use anchors (`^...$`) to require a whole-string
match. Pattern mismatches are verified; unsuccessful inversion raises a structured
`GenerationError` instead of returning a matching value. Obvious universal patterns
(such as `(?s).*`) are excluded from automatic planning, and explicit mismatch
requests raise `PlanningError`.

`MultipleOf` requires a finite positive divisor. For floats, a quotient within
`1e-9` of an integer is treated as a multiple (no relative tolerance). Integer
`NOT_MULTIPLE` requests for divisors such as `1` or `0.5`, which divide every integer,
raise `PlanningError` and are excluded from automatic planning. A bounded range
without a representable multiple raises `GenerationError` with code `no_multiples_of`.

Only one `Pattern` is supported per string field. Combined length and pattern
constraints must have a feasible match; failed generation raises an error.
Numeric invalid values need not be adjacent to a bound. Floats may produce
infinity for an invalid upper-bound case. Integer generation uses signed
64-bit bounds rather than the entire unbounded Python integer domain.

## Bytes

Standard `bytes` fields generate native byte sequences with values from the full
byte range (0–255). `MinLength` and `MaxLength` count bytes and work through
`Annotated`, dataclass metadata, and Pydantic `Field(min_length=..., max_length=...)`.

```python
from dataclasses import dataclass
from typing import Annotated

from conformly import MaxLength, MinLength, V, case, path

@dataclass
class Packet:
    payload: Annotated[bytes, MinLength(2), MaxLength(16)]

packet = case(Packet, seed=42)
invalid = case(Packet, valid=False, target=path("payload").violate(V.TOO_SHORT))
```

Generation is reproducible with `seed`, including collections and nested models.
`TOO_SHORT` produces `min_length - 1` bytes; `TOO_LONG` produces `max_length + 1`.
`MaxLength(0)` generates `b""`. Without an upper bound, valid lengths range from
`min_length` (default 0) to `min_length + 50`. Negative lengths, empty length
ranges, and unsupported constraints such as `Pattern` raise `SchemaError`.

## Temporal values

Standard `datetime.datetime`, `datetime.date`, `datetime.time`, and
`datetime.timedelta` fields generate native Python values, including inside
collections and nested models. Generation is reproducible with `seed`.

Use `GreaterThan`, `GreaterOrEqual`, `LessThan`, and `LessOrEqual` with bounds
of the same type as the field:

```python
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Annotated

from conformly import GreaterOrEqual, LessThan, V, case, path

@dataclass
class Booking:
    day: Annotated[date, GreaterOrEqual(date(2026, 1, 1)), LessThan(date(2027, 1, 1))]
    duration: Annotated[timedelta, GreaterOrEqual(timedelta(hours=1))]

booking = case(Booking, seed=42)
invalid = case(Booking, valid=False, target=path("day").violate(V.BELOW_MIN))
```

Bounds also work in dataclass metadata and Pydantic `Field(gt=..., ge=...,
lt=..., le=...)`. Empty or incompatible ranges raise `SchemaError`.
`BELOW_MIN` and `ABOVE_MAX` produce the nearest value outside the valid range:
one day for `date`, one microsecond for the other types. A violation beyond
Python's representable limits raises `PlanningError`.

Unconstrained `datetime` and `time` values are naive. Aware `datetime` bounds
are compared as UTC instants and produce aware UTC values; mixing aware and
naive bounds is rejected. `time` bounds must be naive and describe a linear
interval within one day, without wrapping across midnight. Other temporal
constraints, including `MultipleOf`, are not supported.

## Formats and collection compatibility

`Email`, `IPv4`, `IPv6`, `IPvAny`, `Url`, and `HttpUrl` are public string marker
types. `HttpUrl` uses HTTP/HTTPS; `Url` supports several schemes. IP types reject
length constraints. All format types reject `Pattern`. Email and URL types accept
length constraints, with [known edge cases](generation.md#guarantees-and-known-limitations).
For example, generate an HTTP endpoint and reject an unsupported scheme:

```python
from dataclasses import dataclass

from conformly import HttpUrl, Url, V, case, path


@dataclass
class Links:
    endpoint: HttpUrl
    resource: Url


payload = case(Links)
assert payload["endpoint"].startswith(("http://", "https://"))
invalid = case(
    Links, valid=False, target=path("endpoint").violate(V.WRONG_URL_SCHEME)
)
assert not invalid["endpoint"].startswith(("http://", "https://"))
```

UUID generation returns canonical lowercase version-4 UUID strings; format violations return strings.
UUID constraints are not interpreted as configurable length or pattern rules.

Fixed tuples cannot change length; incompatible size bounds raise `SchemaError`.
Empty-only collections do not offer element violations. Uniqueness and finite
key domains can make requested sizes infeasible; generation raises a structured
error rather than silently returning a smaller collection.

[Violation selection](strategies.md) · [API reference](api-reference.md)
