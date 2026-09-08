# Test audit (#95)

This audit restores executable coverage without the broader end-to-end
reorganization tracked in [#101](https://github.com/nashabanov/conformly/issues/101).

## Collection

Twenty functions in `tests/test_integration/test_end_to_end.py` were nested inside
`test_generates_invalid_tuple_element`. They are now module-level tests without
an unused `self` argument. All twenty pass independently. The collection guard
in `tests/test_collection.py` rejects test functions hidden inside another function.

To inspect the restored tests:

```sh
uv run -m pytest tests/test_integration/test_end_to_end.py --collect-only -q
```

## Expectations and defects

| Check | Classification | Action |
| --- | --- | --- |
| Twenty previously hidden tests | Collection defect; assertions pass once collected | Restore scope and signatures; check collection explicitly |
| Valid Pydantic special types and EmailStr | Stale `xfail`; existing assertions pass | Remove markers; validate payloads with Pydantic |
| Invalid UUID parsing | Stale exception expectation | Expect `ValueError` from `uuid.UUID`, not Conformly's `GenerationError` |
| Planner model indexes | Order-dependent fixture: one test relied on another to build shared indexes | Create a fresh indexed model fixture for each test |
| Empty/root URL path | Flaky expectation: 80 random samples need not include either boundary | Control path length and check both boundary cases explicitly |
| Nested-quantifier regex | Nondeterministic expectation; a matching candidate is legal | Test retry exhaustion with controlled oversized candidates and test acceptance of a matching candidate separately; this is not a regex execution-time guarantee |
| Invalid Pydantic special types | Ineffective check: `suppress(ValidationError)` accepted both valid and invalid results | Require `ValidationError` across fixed seeds |
| AnyUrl wrong scheme | Product defect exposed by validation: custom alphabetic schemes are valid | Generate a syntactically invalid scheme for unrestricted URLs |
| HttpUrl wrong format | Product defect exposed by validation: Pydantic accepts and normalizes `http:/broken` | Remove that candidate from invalid-format generation |
| Explicit-path reproducibility and DSL/string equivalence | Checks only verified short strings | Compare complete payloads using identical seeds; seeded generation was fixed in #96 |
| Duplicate list violation | Conditional assertion could skip verification | Select `items::duplicate` explicitly and require an actual equal pair |

No existing `xfail` markers remain. `xfail_strict = true` makes future unexpected
passes fail both local checks and CI. Any future expected failure should include
a specific reason and linked defect, with `strict=True`; do not use blanket markers
to hide failures discovered by restoring collection.

## Collection checks requiring coordinated fixes

The following gaps are deliberately recorded for
[#97](https://github.com/nashabanov/conformly/issues/97), which owns collection size,
retry exhaustion, and structural uniqueness:

- `test_unique_items_with_unhashable_values` generates identical dictionaries but
  asserts only length. It does **not** establish uniqueness. Replace its assertions
  alongside the generator fix, covering repeated candidates followed by distinct
  values and an exhausted finite domain.
- `TestListGeneration.test_items_are_unique_and_valid` uses random model fields
  with a large value space; collisions are unlikely even if deduplication is absent.
  Add deterministic collisions and check structural equality, not `repr` identity.
- `TestListGeneration.test_tags_are_unique_strings` has the same low-collision
  limitation. Pair it with finite-domain and exact-size coverage for normalized
  sets and frozensets.

The duplicate-violation assertion now always executes, but preserving an allowed
collection length while inserting duplicates belongs to
[#98](https://github.com/nashabanov/conformly/issues/98). This audit does not certify
those unresolved collection guarantees or turn incorrect behavior into a new
successful assertion.
