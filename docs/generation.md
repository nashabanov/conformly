# Generation

## One payload or a batch

`case(Model)` returns a `dict[str, Any]`. `cases(Model, count=10)` returns a
list of dictionaries. Both default to `valid=True`, `strategy="first"`, `target=None`, and
`seed=None`; `cases()` defaults to `count=1`.

Models are schemas, not constructors: Conformly does not instantiate or run
model validators. Results may contain native bytes, temporal values,
and tuples, so they are not necessarily JSON serializable.

For valid generation, leave `strategy` at its default. Explicit strategies,
type mismatch flags, structural flags, and tracing are invalid-mode options;
using them with `valid=True` raises `GenerationError`.

## Supported types

| Annotation | Generated value |
| --- | --- |
| `str`, `int`, `float`, `bool`, `bytes` | Native Python value |
| `Literal[...]`, `Enum` | An allowed value; enums produce member values |
| `UUID` | Canonical lowercase version-4 UUID string |
| `datetime`, `date`, `time`, `timedelta` | Native temporal value |
| `Email`, `IPv4`, `IPv6`, `IPvAny`, `Url`, `HttpUrl` | String |
| Supported model | Dictionary, recursively |
| `list[T]` | List |
| `set[T]`, `frozenset[T]` | List with uniqueness semantics |
| `tuple[T1, T2]`, `tuple[T, ...]` | Tuple |
| `dict[K, T]` | Dictionary; keys are `str` or Enum/Literal-compatible |
| `T | None`, `Optional[T]` | Nullable field; see priority below |

Collections must be parameterized. General unions such as `int | str` are
unsupported. Use [integrations](integrations.md) for supported model declarations.

## Nested models and collections

Constraints on nested fields are discovered recursively. Supported adapters
can be mixed, including models inside lists and dictionary values.
Use dotted field names such as `profile.email` or `items.price` to target a
nested field. Collection indices and dictionary keys are not selectable paths.
See [nested_models.py](../examples/nested_models.py).

Fixed tuples retain their order and length. Element constraints belong on
individual element annotations; collection size constraints belong on the
collection. Sets and frozensets intentionally produce lists.

## Reproducibility

Integer seeds, including `0` and negative values, make `case()` and `cases()`
reproducible for internal generation, including nested models and UUID values.
The same model, options, and seed produce the same payloads. User-provided default
factories run once per generated field and must themselves be deterministic;
the seed does not control their randomness or external state.

This is not a promise of identical values across library versions. Use a seed
to reproduce a scenario rather than hardcoding generated values.

## Optional Fields and Defaults

- For untargeted fields, priority is **override → nullable `None` → model default
  or default factory → generation**. Nullable fields currently always return `None`
  without an override, even with a non-`None` default; their factories are not called.
- Model defaults, factory results and overrides are trusted and returned without
  validation. `valid=True` guarantees the validity of generated values, not of
  caller-supplied data. An invalid supplied value can also make an unrelated field
  invalid when generating a negative case.
- Invalid targets bypass their defaults, nullable priority and overrides. Other
  fields retain the priority above. Default factories are called once per generated
  payload when selected by this priority; attrs factories requiring `self` are unsupported.
- TypedDict `NotRequired[T]` controls key presence independently of whether `T`
  accepts `None`. Valid generation currently includes these keys with values of `T`;
  `NotRequired[int]` does not become a present `None`.
- `MISSING_FIELD` is offered only for required fields: nullable required fields can
  be removed, but fields with defaults and TypedDict `NotRequired` keys cannot.
  `EXTRA_FIELD` is offered for Pydantic only with `extra="forbid"`; `ignore` and
  `allow` accept extra data. Other adapters treat undeclared keys as structural violations.
- A target needs an applicable semantic, type or structural violation; impossible
  explicit requests raise `PlanningError`.

## Guarantees and known limitations

- Generated values respect supported constraints, subject to the format-generator
  limitations below. Supplied defaults and overrides are not validated.
- Unique collections use structural comparison for unhashable values. Generation
  may exhaust retries; it raises `GenerationError` instead of returning a short
  or duplicate-filled collection. Finite domains cap optional sizes; impossible
  required sizes raise `impossible_collection_size`.
- Cyclic model references and nested collections such as `list[list[T]]` are unsupported.
- No fine-grained control over the collection index or dictionary entry to invalidate.
- Arbitrary user validators, attrs validators/converters, and Pydantic aliases
  are not generation rules. Output uses declared field names.
- Email and URL generators use a limited set of formats and domains, not the full
  RFC domains. Tight length bounds can produce values outside the requested
  bounds; Email length violations can also fail to cross the requested boundary.
  Avoid relying on these edge cases for validation coverage. Plain `str` with
  supported constraints is an alternative when testing length alone.
- Conformly complements schema-driven validation tests; it does not replace
  Hypothesis or explore every possible input.

[Invalid generation contract](strategies.md#invalid-generation-contract) ·
[Constraints](constraints.md) · [API reference](api-reference.md)

Explicit invalid targets use `target=path("field")`, optionally refined with
`.violate(V.X)`. They require `strategy="first"`; targeted `cases()` calls require
`count=1`. Valid generation requires `target=None`. See the
[selection contract and migration](api-reference.md#migration-before-10).
