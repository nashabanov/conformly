# Invalid generation strategies

## Selection and precedence

With `valid=False`, a strategy selects eligible paths. Eligibility requires
an applicable semantic violation, or an enabled type/structural violation.
No eligible paths raises `PlanningError` (`no_violation_candidate`).

| Strategy | `case()` | `cases()` |
| --- | --- | --- |
| `"first"` (default) | First eligible path | First `count` distinct eligible paths |
| `"random"` | Random eligible path | `count` distinct randomly sampled paths |
| `"all"` | Unsupported | One case per eligible path; ignores `count` |
| `"all_violations"` | Unsupported | One case per available violation per eligible path; ignores `count` |

`strategy` accepts only these names. Unknown names, dotted paths, `::` strings,
and selectors passed as strategy raise `GenerationError` (`unsupported_strategy`).
Use `target=path("field")` to select exactly one field, optionally refined with
`.violate(V.X)`. A target requires `valid=False` and `strategy="first"`.
For `cases()` it also requires `count=1`; other counts raise an API error.
Raw strings are not accepted as targets.

`count` must still be at least one when ignored. `first` and `random` raise
`too_many_requested` if `count` exceeds eligible paths. Randomness selects paths,
not violation types. Repeated calls can select the same path.

Without an explicit violation, priority is **structural → type → semantic**.
Within semantic violations, duplication and collection sizes precede numeric
bounds, format errors, string lengths, patterns, and closed-set violations.
Use an explicit violation when the exact failure matters.

`allow_type_mismatch=True` adds type mismatches to eligible scalar/collection
fields and gives them priority over semantic violations. Automatic structural
selection requires `cases(..., strategy="all" or "all_violations",
allow_structural_violations=True)`. Missing fields take priority over semantic
violations; extra-field cases are added for models that reject undeclared fields.
`all_violations` includes type and structural violations only when enabled.

Explicit `target=path("field").violate(V.TYPE_MISMATCH)` or
`.violate(V.MISSING_FIELD)` enables the corresponding capability during path
eligibility checking as well as violation planning. No redundant flag is needed,
including for unconstrained fields. Only the requested path is selected;
nested model objects do not support type mismatches, and nonrequired fields
cannot be removed. Unknown or ineligible targets raise structured `PlanningError`.
`case()` has no structural flag. Explicit extra-field targeting has no public
named path; use structural enumeration.

Common type mismatch outputs are:

| Field type | Mismatch output |
| --- | --- |
| String | Integer |
| Integer, float, boolean | String |
| Enum/Literal | Float |

## Paths and explicit violations

```python
from dataclasses import dataclass
from typing import Annotated

from conformly import MinLength, V, case, path


@dataclass
class Profile:
    name: Annotated[str, MinLength(3)]


@dataclass
class User:
    profile: Profile


invalid = case(
    User, valid=False,
    target=path(User, lambda u: u.profile.name).violate(V.TOO_SHORT),
)
assert len(invalid["profile"]["name"]) < 3
```

Use `target=path("profile.name").violate(V.TOO_SHORT)` for the equivalent
string-path selector. String paths are relative to the root model.
The lambda form executes against an attribute proxy, so it works without source
code in REPLs and notebooks too. The model argument provides editor type hints;
it does not validate membership. Generation validates the resulting path.
Only attribute chains are supported; indexing and method calls raise errors.

For models inside lists or dictionary values, a path such as `items.price`
targets one generated model entry. For scalar collections, target the collection
itself: `path("prices").violate(V.BELOW_MIN)`. The planner picks the first
compatible key, value, or tuple element, then generation chooses an entry where
applicable. An index cannot be specified.

## Invalid Generation Contract

For `case(Model, valid=False, target=path("<field>"))`:

- **Exactly one field is targeted** (the one specified by `target`).
- **The generator will violate constraints** for that field, making it invalid.
- **Inside collections**, planning selects a compatible dictionary key, value, or
  element before generation. Fixed tuples retain their length and order; unrelated
  elements, keys, values, and model fields remain valid.
- **Only the selected violation is guaranteed on its target**. Other constraints
  on that same target are not guaranteed to remain satisfied. A `DUPLICATE`
  violation preserves an allowed collection length; collections with a maximum
  size below two cannot be targeted for duplication.
- **Explicit impossible or unsupported violations raise `PlanningError`**;
  empty-only collections do not offer element violations.
- **For numeric bounds**, invalid values may violate the lower or upper bound (e.g., `age > 120` or `age < 18`).
- **For float bounds**, invalid generation may produce `inf` when violating the upper boundary.

Request an exact violation with `target=path("items").violate(V.BELOW_MIN)` or
`target=path(Model, lambda m: m.items).violate(V.BELOW_MIN)`. Otherwise, the planner uses
violation priority and chooses the first compatible key, value, or tuple element.

Here “minimal” means one planned target, not the smallest possible failing value.
Defaults and overrides can introduce unrelated invalid data; format-generator
edge cases are listed in [Generation](generation.md#guarantees-and-known-limitations).

## Violation reference (`V`)

The enum is public; not every member applies to every field.

| Members | Applicable target |
| --- | --- |
| `BELOW_MIN`, `ABOVE_MAX` | Numeric or temporal bound |
| `NOT_MULTIPLE` | Numeric `MultipleOf` with a feasible nonmultiple |
| `TOO_SHORT`, `TOO_LONG` | String or bytes length (not collection size) |
| `PATTERN_MISMATCH` | Plain string pattern |
| `WRONG_EMAIL_FORMAT` | `Email` |
| `WRONG_IP_FORMAT` | `IPv4`, `IPv6`, `IPvAny` |
| `WRONG_URL_SCHEME` | `Url`, `HttpUrl` |
| `WRONG_URL_FORMAT` | `HttpUrl`; not offered for `Url` |
| `WRONG_UUID_FORMAT`, `WRONG_UUID_CHARACTER` | UUID; invalid result is a string |
| `NOT_ALLOWED_VALUE` | Enum/Literal closed set |
| `TOO_LESS_ITEMS`, `TOO_MANY_ITEMS` | Collection size; variadic tuples only |
| `DUPLICATE` | Unique list/set/frozenset with capacity for two entries |
| `TYPE_MISMATCH` | Enabled type violation; not a nested model object |
| `MISSING_FIELD` | Required field with structural planning enabled |
| `EXTRA_FIELD` | Structural enumeration of models rejecting extra fields |
| `NONE_FOR_NOT_OPTIONAL` | Exported enum member, currently not offered by planning |

Each enum value is its lowercase string spelling, e.g. `V.BELOW_MIN.value`
is `"below_min"`. See [constraints](constraints.md) for impossible boundaries
and [errors](advanced.md#error-handling) for diagnostic codes.
