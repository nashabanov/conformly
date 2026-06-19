# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026.06.20

### Added
- **Overrides support** in `case()` and `cases()` to explicitly set field values
    - Syntax example `path(T, lambda t: t.name).set("name")`
    - Overrides has higher priotity than field default

### Changed
- Now `path` uses proxy-object instead of ast parsing


## [0.6.0] - 2026.06.13

### Added
- **Typed path selection** - `path()` now accepts `lambda` for type-safe field selection
  - Example: `path(User, lambda u: u.profile.email)`
  - String-based paths remain support

## [0.5.0] - 2026.06.10

### Added
- **Basic `attrs` adapter** - support for attrs models as source for generation *(Note: native `attrs` validators are not yet supported and will be added later)*
- **Cross-adapter parsing** - now parser uses adapters registry for nested models, so schemas like `dataclass` inside `pydantic.BaseModel` supported
- **TypedDict adapter** - support for parsing `TypedDict` schemas, including required/optional fields via `NotRequired` / `Required`


## [0.4.0] - 2026.05.09

### Added
- **Unified exception hierarchy** — all library errors now inherit from `ConformlyError`, providing consistent interface for error handling and logging.
- **Specialized exception classes**:
  - `SchemaError` — invalid or malformed schema definitions.
  - `ResolutionError` — failures during schema reference resolution or type mapping.
  - `PlanningError` — invalid task configuration or impossible violation combinations.
  - `GenerationError` — runtime failures during synthetic data generation.
- **Structured error context** — every exception includes:
  - `message: str` — human-readable description.
  - `context: dict[str, Any]` — machine-readable diagnostic data (e.g., `code`, `field`, `constraint`, `strategy`).
- **Collection-level constraints support**:
  - `MinItems(n)` — minimum number of elements
  - `MaxItems(n)` — maximum number of elements
  - `UniqueItems(bool)` — enforce uniqueness of elements (for `dict` will ingnore)
- **Path DSL for explicit field targeting**: `path("field.name").violate(V.TOO_SHORT)` explicit violation targeting via DSL
- **Violation type alias**: `V` — shorthand for `ViolationType` enum used in DSL expressions
- **Basic `dict` support** — Added generation for `dict[K, V]`, where `K` must be `str` or `Enum`, and `V` accepts `Any`.

### Changed
- **Public API error handling** — functions `case()`, `cases()`, and low-level pipeline stages now raise `GenerationError` or `PlanningError` instead of built-in exceptions. This enables precise `except` clauses and structured logging.
- **`set[T]` and `frozenset[T]` types are now normalized** to list-based generation with UniqueItems(True) semantics, ensuring deterministic output format and consistent constraint handling across collection types
- **Parser module refactored**:
  - Unified IR building logic under `parser/core`.
  - Introduced a centralized type analysis pipeline.
  - Added `ElementSpec` for standardized type representation.


## [0.3.10] - 2026.04.11

### Added
- **Full support for `multiple_of` constraint**. Added `MultipleOf` constraint in conformly-style semantics and `Field(multiple_of=...)` support for Pydantic models. Values are now generated respecting the step, including invalid value generation (`NOT_MULTIPLE` violation).
- **Special string semantic types**. Introduced `Email`, `IPv4`, `IPv6`, `IPvAny`, `Url`, `HttpUrl` as semantic markers (subclasses of `SpecialStr`) for type-safe schema definitions.
- **Basic `UUID` support**. Implemented canonical RFC 4122 v4 generation Fully integrated with the violation system (`TOO_SHORT`, `TOO_LONG`, `WRONG_UUID_FORMAT`, `WRONG_UUID_CHARACTER`).
- **Specialized generators**. Implemented realistic data generation for new string semantics.
- **Constraint composition**. Some special types (`Email`) support `MinLength`/`MaxLength` constraints (e.g., `Annotated[Email, MinLength(10)]`), while `Pattern` is restricted to avoid semantic conflicts.
- **Basic `list[T]` support**. Generation of `list[str]`, `list[Annotated[T, Constraint]]`, and `list[Model]` with automatic element-wise constraint enforcement.

### Changed
- **Type resolution architecture**. `extract_runtime_type_and_constraints` now preserves semantic types (e.g., `Email`) for generator routing, instead of collapsing them to `str`.
- **StringSemantic extensibility**. `StringSemantic.kind` now accepts extended `FieldKind` values (`EMAIL`) for specialized generator dispatch.
- **New module `fields`**. Contains special string markers and registry for type mapping with `pydantic` types and field_kinds.
- **Collection-aware parsing**. New `collection_type` field in `FieldSpec` cleanly separates container types from leaf types, unifying type extraction across adapters.
- **BREAKING**: public API was made flatten (constraints, fields and core functions now imports from `conformly` main module)
- **Hide internal logic** in `_internal` module.


## [0.3.9] - 2026.03.21

### Added
- **Deterministic generation** new `seed: int | None = None` parameter in `case()` and `cases()` for reproducible test data
- **GenerationContext** - immutable context object passed through entire generation pipeline
- **pydantic default_factory support** - save `callable` object and call it at generation stage

### Changed
- **Internal architecture** - all generators now receive `GenerationContext` instead of raw `rng`


## [0.3.8] - 2026.03.09

### Added
- **all_violations** srategy - generates case for every allowed violations including constraints, structural and type violations (ignores count)
- **New syntax** for explicit violation type selection: field_name::violation_type (e.g., "username::too_short")

### Changed
- **Violation priority**:
    - Added `_VIOLATION_PRIORITY` tuple for sorting
    - **BREAKING**: Generator choose first violation from task
- **BREAKING**: added explicit mapping to deterministically choose incompatible types.
- **ViolationType enum** now uses string values instead of auto()


## [0.3.7] - 2026.03.03

### Added
- **Internal benchmarking infrastructure** for dataclasses and pydantic models (Makefile, pytest marks), benchmark tests

### Changed
- **lru_cache** for `resolve()` and `parse()` operations to improve pipeline speed
- **Pre-calculated field indexes** in `ResolvedModel` (`field_map`, `constrained_paths`, etc.) to remove multiple DFS traversals during planning and resolving
- **Optimized generate_invalid** logic by splitting loops, removing tuple allocations, and simplifying recursion
- **`ResolvedField` refactor** to store `FieldSpec` directly instead of copying values

## [0.3.6] - 2026.02.18

### Added
- **`allow_structural_violations` flag for `cases()`** API to abable field missing and extra fields for invalid generation
- **Validation guard**: Structural violations available only with `strategy="all"` other options raises `ValueError`
- **`MISSING_FIELD`** available for every field like `TYPE_MISMATCH`
- **`EXTRA_FIELD`** adds only one time for model/nested model

## [0.3.5] - 2026.02.15

### Added
- **`allow_type_mismatch` flag for `case()` and `cases()`** APIs to enable type mismatch violations (e.g., string instead of int) when generating invalid examples
- **Support for `TYPE_MISMATCH` violation** in `planner` and `generator` — becomes an available option alongside semantic constraints when the flag is enabled
- **Type mismatch semantics factory** in resolver module for generating incorrect-type values
- **Validation guard**: raises `ValueError` when allow_type_mismatch=True is combined with valid=True

### Changed
- `bool` and `object` fields can now be violated via type mismatches when `allow_type_mismatch=True`; `NotImplementedError` is raised only when attempting to violate these types with `allow_type_mismatch=False` (no semantic constraints available)

## [0.3.4] - 2026.02.09

### Added
- **Pydantic parsing adapter** as optional adapter (availiable only with `pip install conformly[pydantic]`)
- Unit and integration tests for Pydantic adapter
- Dedicated CI workflow stages for core and Pydantic-enabled test runs
- Pydantic dependency made fully optional via `[pydantic]` extra

### Changed
- **Architectural refactoring**: extracted reusable parsing logic from dataclass adapter into framework-agnostic modules:
  - `parsing/type_analysis.py` — type resolution utilities
  - `parsing/constraints.py` — constraint extraction functions
- Slimmed down `parsing/adapters/dataclass.py` to contain only framework-specific logic

### Known Limitations
- `default_factory` support not yet implemented for dataclass/Pydantic fields

## [0.3.3] - 2026.02.01

### Added
- **Full support for closed-set types** (`Literal` from `typing` and classical `Enum`)
- **Constraint type `OneOf`** (for both `Literal` and `Enum` representation after parsing,
but can be used as part of real model)
- **Violation strategy `NOT_ALLOWED_VALUE`** for generating values outside allowed sets
- Early validation for
    - empty `Literal` and `Enum`
    - invalid constraint combinations with closed-set types

### Changed
- `Oneof` (closed-set types) is now treated as independent terminal constraint.
Combinig `Literal`/`Enum` with other constraints results in a parsing error.


## [0.3.2] - 2026.01.29

### Changed
- Refactored internal collections to use `tuple` instead of `list` for
  immutable data structures. **No changes to public API or runtime behavior**.


## [0.3.1] - 2026-01-28

### Added
- Semantic relover  (`ModelSpec -> ResolvedModel`)
- Field semantics layer that stores executable representation of constraints
- Field level planner for invalid generation that select constrained violations based on field semantic
- Session level planner that search for fields allowed for violating for selected strategy

### Changed
- Restructured generation pipeline to include resolver and planner stages (`model -> parser -> resolver -> planner -> generator -> dict`)
- Removed strategy planning and fields searching logic from `core.py` now its `planner` responsibility
- Removed bounds calculating from `generator` now is works with semantics and execute pre-calculated violations
- Moved common types and constants in `types.py`
- Field violations now selecting randomly

### Fixed
- `nan`/`inf` handling for numeric bounds calculation and generation
- Some incorrect bounds calculation cases



## [0.3.0] - 2026-01-21

### Added
- Support for **nested_models** (tree structures) in parsing and generation
- Support for selecting nested field using dotted path syntax
  (e.g. `strategy="user.profile.email"`)

### Changed
- Field selection strategies now operate over the full tree of constrained fields (DFS order)

### Fixed
- Fixed incorrect invalid value generation in `int` and `float` generators when only one bound was present


## [0.2.0] - 2025-12-25

### Added
- **Typed constraint system**: Replaced `ConstraintSpec` with concrete, type-safe constraint classes:
    - `MinLength`, `MaxLength`, `Pattern` for strings
    - `GreaterThan`, `GreaterOrEqual`, `LessThan`, `LessOrEqual` for numeric (`int` and `float`)
- Full compability with new syntax `Annotated[T, MinLength(10)]` (recommended)
- Support for mixed constraint definitions (typed + strings + metadata)

### Changed
- **BREAKING**: Removed `ConstraintSpec` from public API and internal logic
- **BREAKING**: Constraint validation now happened in parse time (not at generation time)
- Refactored internal architecture:
    - Separeted constraint definitions (`constraints/`) from data specs (`specs/`)
    - Moved `ConstraintType` and validation sets to `constraint/types.py`

### Removed
- Deprecated string only constraint syntax in internal logic (still supported for users)


## [0.1.0] - 2025-12-18

Initial release of **conformly**.

### Added
- Core generator engine (`case` and `cases` functions).
- Support for generating valid/invalid data from standard Python `dataclasses`.
- Constraint extraction from:
  - `Annotated[T, ConstraintSpec(...)]`
  - `Annotated[T, "min_length=5"]` (string shorthand)
  - `field(metadata={"ge": 0})`
- Supported constraints:
  - String: `min_length`, `max_length`, `pattern` (regex).
  - Numeric (int/float): `gt`, `ge`, `lt`, `le`.
  - Boolean: basic true/false generation.

### Known Limitations
- Invalid generation strategy `"random"` does not guarantee violation on every call (statistical approach).
- Invalid generation for float bounds may produce `inf` when violating upper bounds.
- Deterministic selection of specific violated constraint is not yet supported.
