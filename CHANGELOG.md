# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.3.3] - 2025.02.01

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


## [0.3.2] - 2025.01.29

### Changed
- Refactored internal collections to use `tuple` instead of `list` for
  immutable data structures. **No changes to public API or runtime behavior**.


## [0.3.1] - 2025-01-28

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



## [0.3.0] - 2025-01-21

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
