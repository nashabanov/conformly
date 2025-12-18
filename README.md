# conformly

[![Python Versions](https://img.shields.io/pypi/pyversions/conformly.svg)](https://pypi.org/project/conformly/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Declarative test data generator for Python. Turns data models (now only dataclasses) and type constraints into valid fixtures and negative test cases.**

`conformly` allows you to define your data schema *once* using standard Python dataclasses and `Annotated` constraints, and instantly generate rigorous test data. It replaces verbose factory patterns with a smart, schema-aware generator that supports both happy-path and edge-case testing.

Instead of writing separate factory classes or hardcoding test dictionaries, Conformly:

- **Extracts constraints** from your dataclasses (length bounds, regex patterns, numeric ranges)
- **Generates valid data** strictly adhering to all constraints for happy-path testing
- **Generates invalid data** intelligently violating constraints for negative testing and fuzzing
- **Bridges static typing and dynamic testing** — your schema is the single source of truth

## Key Features

- **Zero Boilerplate:** Works directly with standard `dataclasses`. No need to learn a new DSL.
- **Constraint-Aware:** Respects `min_length`, `max_length`, `pattern` (regex), and numeric bounds (`gt`, `ge`, `lt`, `le`).
- **Negative Testing Built-in:** Generates edge cases and boundary violations for robust error handling tests.
- **Flexible Definitions:** Supports constraints via `Annotated` (explicit or shorthand) and `field(metadata=...)`.
- **Pure Python:** Lightweight, no heavy dependencies, works with standard library tools.

## Install

```bash
pip install conformly
# or with uv
uv add conformly
```

## Quickstart

Define a model:

```python
from dataclasses import dataclass, field
from typing import Annotated
from conformly import case, cases


@dataclass
class User:
    username: Annotated[str, "min_length=3"]
    email: Annotated[str, "patter"=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"]
    age: Annotated[int, "ge=18", "le=120"]
```

Generate valid data:

```python
user = case(User, valid=True)
# -> {"username": "Abc", "email": "x@y.z", "age": 42}
```

Generate an invalid case for a specific field:

```python
bad_user = case(User, valid=False, strategy="age")
# bad_user["age"] is outside 18..120 (either < 18 or > 120)
```

Generate many cases:

```python
items = cases(User, valid=True, count=10)
```

## Use Cases
```python
case(Model, ...) # single generated object
cases(Model, ...) # list of generated objects
```

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
```

### Database Seeding
```python
# Generate realistic test data respecting schema constraints
products = cases(Product, valid=True, count=1000)
db.insert_many("products", products)
```

### Fuzzing & Property-Based Testing
Conformly is not a replacement of Hypotesis, but a complementary tool
for schema-driven testing and negative case generation.
```python
# Generate random invalid data to stress-test validation
for _ in range(500):
    invalid = case(Model, valid=False, strategy="random")
    assert validate(invalid) is False  # Should always reject
```

## Supported Constraints

### String
- `min_length` — minimum string length
- `max_length` — maximum string length
- `pattern` — regex pattern (must match)

### Integer / Float Bounds
- `gt` — strictly greater than
- `ge` — greater than or equal
- `lt` — strictly less than
- `le` — less than or equal

### Boolean
- Basic boolean generation (no extra constraints)

## Defining Constraints

### 1) `Annotated[..., ConstraintSpec(...)]` (explicit)

```python
from typing import Annotated
from conformly.specs import ConstraintSpec

username: Annotated[str, ConstraintSpec("min_length", 3)]
age: Annotated[int, ConstraintSpec("ge", 18)]
```

### 2) `Annotated[..., "k=v"]` (shorthand)

```python
title: Annotated[str, "min_length=5", "max_length=200"]
views: Annotated[int, "ge=0"]
rating: Annotated[float, "ge=0", "le=5"]
```

### 3) `field(metadata={...})`

```python
from dataclasses import field

sku: str = field(metadata={"pattern": r"^[A-Z0-9]{8}$"})
stock: int = field(metadata={"ge": 0})
price: float = field(metadata={"gt": 0})
```

## Invalid Generation Contract (Important)

For `case(Model, valid=False, strategy="<field>")`:

- **Exactly one field is targeted** (the one specified by `strategy`).
- **The generator will violate constraints** for that field, making it invalid.
- **If a field has multiple constraints**, the violated constraint may be chosen by generator logic (not necessarily the one you expect).
- **For numeric bounds**, invalid values may violate the lower or upper bound (e.g., `age > 120` or `age < 18`).
- **For float bounds**, invalid generation may produce `inf` when violating the upper boundary.

If you need **deterministic control** over which exact constraint to violate, that is not implemented in 0.0.1 (see Roadmap).

## Optional Fields and Defaults

- If a field is **optional** (`Optional[T]`), valid generation may produce `None`.
- If a field has a **default value**, valid generation returns the default.
- Invalid generation **requires at least one constraint** on the targeted field (raises `ValueError` otherwise).

## Development

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run -m pytest -q
```

Run with coverage:

```bash
uv run -m pytest --cov=conformly --cov-report=term-missing
```

Build & check package:

```bash
uv build
uv run -m twine check dist/*
```

## Roadmap

- **Nested data models**
- **Deterministic invalid generation** - explicitly select which constraint to violate
- **Better regex invalidation** - guarantee that invalid strings don't match patterns
- **More adapters** - pydantic, TypedDict, attrs support
- **More constraints and types** - `multitiple_of`, `Literal`, `list[T]`, `dict[T]` etc.
- **Custom generators** - allow per-field generator overrides

## License

MIT — see `LICENSE` file for details

## Contributing

Contributions welcome! Please:
- Fork the repo
- Create a feature branch
- Add tests for new functionality
- Run `uv run -m pytest` and `uv run -m ruff check .`
- Submit a pull request
