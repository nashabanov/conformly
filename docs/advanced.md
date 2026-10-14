# Advanced usage

## Overrides

```python
from dataclasses import dataclass
from typing import Annotated

from conformly import MinLength, V, case, path


@dataclass
class User:
    name: Annotated[str, MinLength(3)]
    tenant: str


payload = case(User, overrides=[path("tenant").set("test-tenant")])
assert payload["tenant"] == "test-tenant"
invalid = case(
    User, valid=False, target=path("name").violate(V.TOO_SHORT),
    overrides=[path("tenant").set("test-tenant")],
)
assert invalid["tenant"] == "test-tenant"
```

Override values are trusted without schema validation. They override defaults,
but an invalid target bypasses its override. Nested paths apply to matching
fields in generated nested models, including every model item in lists and
dictionary values. The selected invalid field still bypasses its override;
other items retain theirs. Unknown override paths raise
`GenerationError` with `code="invalid_override_path"`, the requested `path`, and
`available` field paths. Every override must be configured with `.set(value)`;
bare or violation-only selectors raise `invalid_override_selector`.
`.set(None)` is an intentional override, including for non-nullable fields, and
bypasses defaults and factories. Duplicate paths use the last supplied value.
Selectors are immutable:
`.set()` and `.violate()` return new selectors and replace the other operation;
do not chain them expecting a combined override and violation.

There is no public custom-generator registry, adapter-registration API, or
configuration object. Use model defaults/default factories and overrides for
custom values. Registries under `_internal` are implementation details.

## Error handling

All `conformly` errors inherit from `ConformlyError`, providing a consistent
interface for debugging and programmatic handling.

Library-raised diagnostic errors carry:

- `message: str` — human-readable description.
- `context: dict` — diagnostic data with a `code` for programmatic checks.

The base exception permits an empty context; exceptions from user factories or
third-party code are not guaranteed to carry Conformly diagnostic codes.

```python
from dataclasses import dataclass
from typing import Annotated

from conformly import MinLength, V, case, path
from conformly.exceptions import PlanningError


@dataclass
class User:
    name: Annotated[str, MinLength(3)]


try:
    case(User, valid=False, target=path("name").violate(V.BELOW_MIN))
except PlanningError as error:
    assert error.context["code"] == "invalid_forced_violation"
    assert "too_short" in error.context["allowed"]
```

| Exception (`conformly.exceptions`) | Meaning | Representative codes |
| --- | --- | --- |
| `SchemaError` | Malformed or unsupported schema/constraints | `unsupported_union`, `inconsistent_constraints`, `invalid_numeric_bounds`, `invalid_length_range`, `invalid_constraint_combination` |
| `ResolutionError` | Unsupported model/type mapping | `adapter_not_found`, `unsupported_field_type`, `invalid_dict_key` |
| `PlanningError` | No feasible negative target | `field_not_found`, `no_violation_candidate`, `no_constraints_field`, `invalid_forced_violation`, `too_many_requested`, `infeasible_collection_target` |
| `GenerationError` | Invalid API options or generation failure | `invalid_override_path`, `invalid_override_selector`, `invalid_count`, `invalid_strategy_for_valid`, `invalid_flag_for_valid`, `unsupported_strategy`, `invalid_target`, `invalid_target_for_valid`, `invalid_strategy_for_target`, `invalid_count_for_target`, `no_multiples_of`, `impossible_collection_size`, `collection_retry_exhausted` |

Diagnostic keys vary by error: e.g. `available` lists paths or violation names,
`allowed` lists applicable violations, and collection errors include requested
and generated sizes. Check `context["code"]` rather than parsing the message.

## Experimental tracing

`Tracer` captures metadata about invalid `case()` generation. This API is
experimental and may change in minor releases.

```python
from conformly import V, case, path
from conformly.tracer import Tracer

# Using User from the override example above:
tracer = Tracer()
payload = case(
    User, valid=False, target=path("name").violate(V.TOO_SHORT),
    seed=42, tracer=tracer,
)
trace = tracer.build()
assert trace.target_path == "name"
assert trace.violation == V.TOO_SHORT
assert trace.generated_value == payload["name"]
```

Tracing is available for `case(..., valid=False)`. The trace describes the selected
target: its dotted path, violation, generated value, seed, and value source. This
applies to DSL and string paths as well as `"first"` and `"random"` selection.
Unrelated fields, defaults, and overrides do not overwrite target metadata. For
`MISSING_FIELD`, the value is the internal `UNSET` sentinel because the field is
absent from the payload.

Enabling tracing leaves payloads, internal RNG consumption, and default factory
call counts unchanged. A reused tracer describes the latest completed generation.

`cases()` does not accept a tracer. A trace exposes `target_path`, `seed`,
`violation`, `generated_value`, and `value_source` (an enum with a string `.value`).
The missing-field sentinel has no public export; inspect the violation and
payload key presence instead of importing the sentinel.

[API reference](api-reference.md) · [Generation](generation.md)
