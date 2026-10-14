# Public API reference

Import the following from `conformly`. The accepted user-facing model argument
is a dataclass, TypedDict, Pydantic, or attrs class; internal spec objects are not
part of this reference. Type notation below describes the public calling forms;
selector instances come from `path()`, not an internal import.

## `case()`

```python
def case(
    model_or_spec: type,
    *,
    valid: bool = True,
    seed: int | None = None,
    strategy: CaseStrategy = "first",
    target: PathSelector | None = None,
    overrides: list[PathSelector] | None = None,
    allow_type_mismatch: bool = False,
    tracer: Tracer | None = None,
) -> dict[str, Any]: ...
```

## `cases()`

```python
def cases(
    model_or_spec: type,
    *,
    valid: bool = True,
    seed: int | None = None,
    strategy: CasesStrategy = "first",
    target: PathSelector | None = None,
    count: int = 1,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
    overrides: list[PathSelector] | None = None,
) -> list[dict[str, Any]]: ...
```

| Argument | Accepted value and behavior |
| --- | --- |
| `model_or_spec` | Model class; required positional argument |
| `valid` | `bool`; choose valid or negative generation |
| `seed` | `int | None`; seeds internal generation |
| `strategy` | `CaseStrategy = Literal["first", "random"]`; `CasesStrategy = Literal["first", "random", "all", "all_violations"]`; see [strategy table](strategies.md#selection-and-precedence) |
| `target` | Selector from `path()`, or `None`; invalid generation only, with `strategy="first"` |
| `overrides` | List of selectors created with `.set(value)` for existing paths, or `None`; `.set(None)` is explicit; duplicates use the last value |
| `count` | `int >= 1`; valid batch size or invalid path-selection count; must be 1 with a target; ignored by enumeration |
| `allow_type_mismatch` | `bool`; enables invalid type planning |
| `allow_structural_violations` | `bool`; `cases()` only; enables structural enumeration or explicit structural requests |
| `tracer` | `conformly.tracer.Tracer | None`; invalid `case()` only |

Only `strategy="first"` and `target=None` are accepted with `valid=True`. Flags are false and
tracer is absent in valid mode. Return values are payloads, not model instances.
See [generation](generation.md) for defaults, nullability, and reproducibility.

## `path()`

```python
path(target: str)
path(target: type[T], expr: Callable[[T], Any])
```

Returns an immutable selector with `raw_path`, `forced_violation`, `override`,
and `has_override`. The presence flag distinguishes `.set(None)` from a bare
selector.
Use `.violate(violation: V)` to select a violation or `.set(value: Any)` to
supply an override. `.set(value)` marks override presence, including for `None`.
Each method returns a new selector and replaces the other operation's
configuration. Attribute-only lambda chains and dotted strings are supported; indices and calls are unsupported.
See [paths](strategies.md#paths-and-explicit-violations).

## Overrides

Override validation is identical in both APIs and generation modes. Unknown paths
raise `GenerationError` with `code="invalid_override_path"`, `path`, and `available`.
Bare, violation-only, or mixed-intent override selectors raise
`GenerationError` with `code="invalid_override_selector"`. Override values remain
trusted; the selected invalid field ignores its override.

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

## Migration before 1.0

Paths and violations are no longer parsed from `strategy`. Use a selector in
`target`; both dotted strings and typed lambdas remain supported.

```python
# Before
case(User, valid=False, strategy="email::too_short")

# After
case(
    User,
    valid=False,
    target=path("email").violate(V.TOO_SHORT),
)
```

Likewise, replace `strategy="profile.email"` with `target=path("profile.email")`
and `strategy=path(...)` with `target=path(...)`. Set `count=1` for targeted
`cases()` calls; larger counts are rejected rather than silently ignored.
There are no compatibility aliases or deprecation warnings.
