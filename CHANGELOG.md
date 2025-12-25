# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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
