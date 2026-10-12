# Public API reference

Import the following from `conformly`. The accepted user-facing model argument
is a dataclass, TypedDict, Pydantic, or attrs class; internal spec objects are not
part of this reference. Type notation below describes the public calling forms;
selector instances come from `path()`, not an internal import.

## `case()`

```python
case(
    model_or_spec,
    *,
    valid=True,
    seed=None,
    strategy="first",
    overrides=None,
    allow_type_mismatch=False,
    tracer=None,
) -> dict[str, Any]
```

## `cases()`

```python
cases(
    model_or_spec,
    *,
    valid=True,
    seed=None,
    strategy="first",
    count=1,
    allow_type_mismatch=False,
    allow_structural_violations=False,
    overrides=None,
) -> list[dict[str, Any]]
```

| Argument | Accepted value and behavior |
| --- | --- |
| `model_or_spec` | Model class; required positional argument |
| `valid` | `bool`; choose valid or negative generation |
| `seed` | `int | None`; seeds internal generation |
| `strategy` | String or selector from `path()`; see [strategy table](strategies.md#selection-and-precedence) |
| `overrides` | List of selectors created with `.set(value)`, or `None` |
| `count` | `int >= 1`; valid batch size or invalid path-selection count; ignored by explicit paths and enumeration |
| `allow_type_mismatch` | `bool`; enables invalid type planning |
| `allow_structural_violations` | `bool`; `cases()` only; enables structural enumeration or explicit structural requests |
| `tracer` | `conformly.tracer.Tracer | None`; invalid `case()` only |

Only `strategy="first"` is accepted with `valid=True`. Flags are false and
tracer is absent in valid mode. Return values are payloads, not model instances.
See [generation](generation.md) for defaults, nullability, and reproducibility.

## `path()`

```python
path(target: str)
path(target: type[T], expr: Callable[[T], Any])
```

Returns an immutable selector with `raw_path`, `forced_violation`, and `override`.
Use `.violate(violation: V)` to select a violation or `.set(value: Any)` to
supply an override. Each method returns a new selector. Attribute-only lambda
chains and dotted strings are supported; indices and calls are unsupported.
See [paths](strategies.md#paths-and-explicit-violations).

## Constraints and marker types

The complete exported constraint set is `GreaterThan`, `GreaterOrEqual`,
`LessThan`, `LessOrEqual`, `MultipleOf`, `MinLength`, `MaxLength`, `Pattern`,
`OneOf`, `MinItems`, `MaxItems`, and `UniqueItems`.
Their constructor arguments, accepted types, and limitations are in
[Constraints](constraints.md#reference).

The exported string marker types are `Email`, `IPv4`, `IPv6`, `IPvAny`, `Url`,
and `HttpUrl`. Use them as field annotations; generated values are strings.
`V` is the violation enum; every member is listed in the
[violation reference](strategies.md#violation-reference-v).
There are no additional public configuration constants.

## Exceptions and tracing

`ConformlyError` is exported from the package root. `SchemaError`,
`ResolutionError`, `PlanningError`, and `GenerationError` are imported from
`conformly.exceptions`. They accept `message: str` and keyword-only
`context: dict[str, Any] | None = None`.

`Tracer()` is imported from `conformly.tracer`. Pass it to invalid `case()`,
then call `.build()` for the trace. See [advanced usage](advanced.md) for
error codes, trace fields, and experimental stability.
