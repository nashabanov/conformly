# conformly

[![CI](https://github.com/nashabanov/conformly/actions/workflows/ci.yaml/badge.svg)](https://github.com/nashabanov/conformly/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/github/nashabanov/conformly/graph/badge.svg?branch=main)](https://codecov.io/github/nashabanov/conformly)
[![PyPI](https://img.shields.io/pypi/v/conformly.svg)](https://pypi.org/project/conformly/)
[![Python Versions](https://img.shields.io/pypi/pyversions/conformly.svg)](https://pypi.org/project/conformly/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha-yellow.svg)](https://github.com/nashabanov/conformly/releases)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


**Declarative test data generator for Python. Turns data models (dataclasses, Pydantic) and type constraints into valid fixtures and negative test cases.**
Define constraints once in type annotations — generate both valid and minimal invalid test data automatically.
No factories, no hardcoded fixtures, no drift when schema changes.

---

## Table of contents

- [Key Features](#key-features)
- [Install](#install)
- [Quickstart](#quickstart)
  - [With dataclasses](#with-dataclasses)
  - [With Pydantic](#with-pydantic)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Invalid Generation Contract](#invalid-generation-contract)
- [Optional Fields and Defaults](#optional-fields-and-defaults)
- [Constraints](#constraints)
  - [Supported Constraints](#supported-constraints)
  - [Defining Constraints](#defining-constraints)
  - [Special String types](#special-string-types)
- [User Cases](#use-cases)
- [Nested Models](#nested-models)
- [Collections](#collections)
- [Development](#development)
- [Changelog](#changelog)
- [License](#license)
- [Contributing](#contributing)

## Key Features

- **Constraint-driven generation** - type constraints act as executable generation rules
- **Minimal invalid cases** - only the targeted field violates constraints; everything else stays valid
- **Schema as single source of truth** - change a constraint → all test data adapts automatically
- **Unified constraint model** - multiple declaration styles normalized internaly
- **Framework adapters** - dataclasses (built-in), Pydantic (optional via `conformly[pydantic]`)

## Install

```bash
# Core functionality (dataclasses support)
pip install conformly

# With Pydantic support
pip install conformly[pydantic]

```

## Quickstart

### With dataclasses

```python
from dataclasses import dataclass
from typing import Annotated
from conformly import case, MinLength, Pattern, GreaterOrEqual, LessOrEqual


@dataclass
class User:
    username: Annotated[str, MinLength(3)]
    email: Annotated[str, Pattern(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
    age: Annotated[int, GreaterOrEqual(18), LessOrEqual(120)]

valid = case(User, valid=True)
# -> {"username": "Abc", "email": "x@y.z", "age": 42}
```

### With Pydantic

```python
from pydantic import BaseModel, Field
from conformly import case

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: str = Field(..., pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    age: int = Field(..., ge=18, le=120)

valid = case(User, valid=True)
# -> {"username": "Abc", "email": "x@y.z", "age": 42}
```

## API Reference
```python
case(
    model,
    *,
    valid: bool,
    seed: int | None = None,
    strategy: str | None = None,
    allow_type_mismatch: bool = False
) -> dict

cases(
    model,
    *,
    valid: bool,
    seed: int | None = None,
    strategy: str = "all",
    count: int | None = None,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False
) -> list[dict]
```
`strategy` values:
- `<field_name>`(legacy) - target specific field for invalidation (for nested fields using dot syntax `"profile.name"`)
- `<field_name>::<violations>`(legacy) - target specific violation for field (syntax `"profile.name::too_long"`)
- **DSL-based targeting** (recommended for violation targeting):
```python
from conformly import path, V

path("user.email").violate(V.TOO_SHORT)
path("profile.name").violate(V.PATTERN_MISMATCH)
```
- `"random"` - choose a random field/constraint to violate
- `"all"` - (for `cases`) produce all minimal invalid variations for the model
- `"first"` - violate the first constrained field (for `case`) or take the first N constrained fields (for `cases`)
- `"all_violations"` - generate one invalid case per every available violations including constraints, structural and type violations (ignores count)

## Error Handling

All `conformly` errors inherit from `ConformlyError`, providing consistent interface for debugging and programmatic handling.

### Structured context
Every exception includes:
- `message: str` — human-readable description
- `context: dict` — diagnostic data with stable `code` for programmatic checks

```python
from conformly import case
from conformly.exceptions import GenerationError

try:
    case(User, valid=False, strategy="email::invalid_type")
except GenerationError as e:
    print(e.message)           # "Unknown violation type 'invalid_type'"
    print(e.context["code"])   # "invalid_violation_type"
    print(e.context["available"])  # ["too_short", "too_long", "pattern_mismatch", ...]
```

## Invalid Generation Contract

For `case(Model, valid=False, strategy="<field>")`:

- **Violation priority**: generator choose first violation type from allowed based on priority (Structural (Missing/Extra) > Type Mismatch > Semantic (Range/Pattern/Value))
- **If `allow_type_mismatch=True`**, the generator may substitute a type mismatch (e.g., string instead of int) in place of a semantic constraint violation for the targeted field

| Type | Mismatch |
|------|------------|
| String | Integer |
| Integer | String |
| Float | String |
| Boolean | String |
| Enum/Literal | Float |

- **If `allow_structural_violations=True`**, generator may substitute field missing in place of any other violations (avaliable only with `strategy="all"`)
- **Exactly one field is targeted** (the one specified by `strategy`).
- **The generator will violate constraints** for that field, making it invalid.
- **If a field has multiple constraints**, the violated constraint may be chosen by generator logic (not necessarily the one you expect).
- **For numeric bounds**, invalid values may violate the lower or upper bound (e.g., `age > 120` or `age < 18`).
- **For float bounds**, invalid generation may produce `inf` when violating the upper boundary.

If you need **deterministic control** over which exact constraint to violate, that is not implemented in yet (see Roadmap).

## Optional Fields and Defaults

- If a field is **optional** (`Optional[T]`), valid generation may produce `None`.
- If a field has a **default value**, valid generation returns the default.
- Invalid generation **requires at least one constraint** on the targeted field (raises `ValueError` otherwise).

## Constraints

### Supported constraints
| Type | Constraint | Pydantic equivalent |
|------|------------|---------------------|
| String | `MinLength(n)` | `min_length=n` |
| String | `MaxLength(n)` | `max_length=n` |
| String | `Pattern(regex)` | `pattern=regex` |
| Numeric | `GreaterThan(v)` | `gt=v` |
| Numeric | `GreaterOrEqual(v)` | `ge=v` |
| Numeric | `LessThan(v)` | `lt=v` |
| Numeric | `LessOrEqual(v)` | `le=v` |
| Numeric | `MultipleOf(v)` | `multitiple_of=v` |
| Closed-set | `OneOf(values)` | `Literal[...]`, `Enum` |
| Collection | `MinItems(n)` | `min_length=n` (for lists in `Field(...)`) |
| Collection | `MaxItems(n)` | `max_length=n` (for lists in `Field(...)`) |
| Collection | `UniqueItems(bool)` | `set[T]`, `frozenset[T]` |

> Important: Pydantic's constr(), conint(), and functional validators are not interpreted as constraints.
> Use Field() parameters for constraint extraction.

### Defining constraints

#### 1) `Annotated[..., Constraint(...)]` (recommended)
> You can use for both model types (dataclasses, Pydantic)
```python
from typing import Annotated
from conformly import MinLength, GreaterOrEqual

username: Annotated[str, MinLength(3)]
```
#### 2) `Annotated[..., "k=v"]` (shorthand string syntax)
```python
title: Annotated[str, "min_length=5", "max_length=200"]
```

#### 3) `Field(...)` (Pydantic only)
```python
from pydantic import Field

username: str = Field(..., min_length=3)
```

#### 4) `field(metadata={...})` (dataclasses only)
```python
from dataclasses import field

sku: str = field(metadata={"pattern": r"^[A-Z0-9]{8}$"})
```
> All syntaxes are fully compatible within their respective frameworks.

### Special String types

`conformly` provides semantic marker types for common string formats. These types enable realistic test data generation while maintaining type safety.


#### Available types
| Type | Description | Pydantic type| Example output | Availiable constraints |
|------|-------------|--------------|----------------|-----------------------|
| `Email` | RFC 5322-compliant email address | `EmailStr` | `user@example.com` | `MinLength`, `MaxLength` |
| `IPv4` | RFC 791-compliant IPv4 address (dotted-quad notation) | `IPv4Address` | `192.0.2.1` | - |
| `IPv6` | RFC 4291-compliant IPv6 address (hex groups with :: compression) | `IPv6Address` | `2001:db8::1` | - |
| `IPvAny` | Either IPv4 or IPv6 address (randomly selected at generation time) | `IPvAnyAddress` | `fe80::1` or `10.0.0.1` | - |
| `Url` | Generic URL with any RFC 3986-compliant scheme | `AnyUrl` |`https://example.com/path` | `MinLength`, `MaxLength` |
| `HttpUrl` | URL with scheme restricted to http or https only | `HttpUrl` |`https://example.com/path` | `MinLength`, `MaxLength` |


#### Usage

```python
from typing import Annotated
from conformly import Email, MinLength

# Basic usage
contact: Email

# With additional constraints
website: Annotated[URL, MinLength(20)]

# Pydantic models (auto-mapped)
from pydantic import BaseModel, EmailStr

class Config(BaseModel):
    admin_email: EmailStr  # Automatically uses Email generator
```

#### UUID support

Standard `uuid.UUID` fields are supported out of the box. Values are generated in canonical RFC 4122 v4 format (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`, lowercase).

```python
import uuid
from dataclasses import dataclass
from conformly import case, path, V

@dataclass
class Session:
    id: uuid.UUID
    user_id: uuid.UUID

valid = case(Session, valid=True)
# -> {"id": UUID("550e8400-e29b-41d4-a716-446655440000"), ...}

invalid = case(Session, valid=False, strategy=path("id").violate(V.TOO_SHORT))
# -> {"id": "550e8400-e29b-41d4-a716-44665544000"}  # TOO_SHORT
invalid = case(Session, valid=False, strategy=path(id).violate(V.WRONG_UUID_CHARACTER))
# -> {"id": "550e8400-e29b-41d4-a71@-446655440000"} # WRONG_UUID_CHARACTER
```

## Use Cases

### API Testing
```python
# Valid payloads for happy-path tests
for _ in range(100):
    payload = case(CreateUserRequest, valid=True)
    response = client.post("/users", json=payload)
    assert response.status_code == 201

# Invalid payloads for error handling tests
invalid = case(CreateUserRequest, valid=False, strategy="age")
response = client.post("/users", json=invalid)
assert response.status_code == 400

# As option create all possible invalid cases for payload in one only line
invalid_payloads = cases(CreateUserRequest, valid=False, strategy="all")
for payload in invalid_payloads:
    response = client.post("/users", json=payload)
    assert response.status_code == 400
```

### Database Seeding
```python
# Generate realistic test data respecting schema constraints
products = cases(Product, valid=True, count=1000)
db.insert_many("products", products)
```

### Fuzzing & Property-Based Testing
Conformly is not a replacement of Hypothesis, but a complementary tool
for schema-driven testing and negative case generation.
```python
# Generate random invalid data to stress-test validation
for _ in range(500):
    invalid = case(Model, valid=False, strategy="random")
    assert validate(invalid) is False  # Should always reject
```

## Nested Models
`Conformly` supports nested models represented as tree structures
(e.g. dataclasses containing other dataclasses).

> Cyclic references between models are not supported

Constraints defined on nested fields are discovered recursively and
can be used for both valid and invalid data generation.

### Model Declaration
```python
from dataclasses import dataclass
from typing import Annotated

from conformly import MinLength, GreaterOrEqual, Pattern

@dataclass
class Profile:
    email: Annotated[str, Pattern(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
    phone: Annotated[str, Pattern(r"^\+[1-9]\d{1,14}$")]


@dataclass
class User:
    name: Annotated[str, MinLength(3)]
    age: Annotated[int, GreaterOrEqual(18)]
    profile: Profile
```

### Generation Example
```python
from conformly import case

valid_data = case(User, valid=True)
print(valid_data)
# {
#     "name": "validname",
#     "age": 25,
#     "profile": {
#            "email": "some@email.com",
#            "phone": "+12025550123"
#         }
# }

invalid_data_by_field = case(User, valid=False, strategy="profile.email")
print(invalid_data_by_field)
# {
#     "name": "validname",
#     "age": 25,
#     "profile": {
#            "email": "nonemailstring",
#            "phone": "+12025550123"
#         }
# }
```

## Collections

### List support

`conformly` supports basic generation of `list[T]` where `T` is a constrained primitive or a nested model.

#### Example

```python
from dataclasses import dataclass
from typing import Annotated
from conformly import case, MinLength, MaxItems, UniqueItems

@dataclass
class Product:
    sku: str
    price: float

@dataclass
class Order:
    tags: list[str]                                                   # list of unconstrained strings
    codes: Annotated[list[Annotated[str, MinLength(5)]], MaxItems(6)] # each element ≥5 chars, max 6 items
    items: Annotated[list[Product], UniqueItems(True)]                # unique nested models

valid = case(Order, valid=True)
# -> {
#   "tags": ["abc", "def"],
#   "codes": ["ABCDE", "FGHIJ"],
#   "items": [{"sku": "...", "price": 10.0}]
# }

invalid = case(Order, valid=False, strategy="codes")
# -> {
#   "tags": [...],
#   "codes": ["ab", "VALID"],  # one element violates MinLength
#   "items": [...]
# }
```

### Set and frozenset support

`set[T]` and `frozenset[T]` are normalized internally to list generation with `UniqueItems(True)` semantics:

```python
@dataclass
class Model:
    tags: set[str]

case(Model)
# -> {"tags": ["a", "b", "c"]}  # always unique
```

This ensures consistent output format (list) while preserving uniqueness guarantees.

### Known limitations

- No nested collections (`list[list[T]]` not supported yet)
- No fine-grained control over which index is violated (random selection only)
- Uniqueness for non-hashable elements (e.g., dicts) is best-effort (based on structural comparison fallback)


## Development

### Setup

Create a virtual environment and install dependencies:

```bash
make install-dev
```
Install with all optional features:

```bash
make install-all
```

### Running tests

Run unit tests:

```bash
make test
```

Run all tests (including benchmarks):

```bash
make test-all
```

Run with coverage:

```bash
make test-cov
```

### Code quality

Run linter:

```bash
make lint
```

Auto-fix lint issues:

```bash
make lint-fix
```

Run type checker:

```bash
make typecheck
```

Run all checks:
```bash
make check
```

### Dependencies managment

Sync dependencies from lockfile:
make sync
Strict sync (CI mode):
make sync-strict
Update dependencies:
make update


## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes and migration guidance.

## License

MIT — see [LICENSE](LICENSE) file for details

## Contributing

Contributions welcome!
- Fork the repo
- Create a feature branch
- Add tests for new functionality
- Run `uv run -m pytest` and `uv run -m ruff check .`
- Submit a pull request
