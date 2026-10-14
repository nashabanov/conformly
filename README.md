# conformly

[![CI](https://github.com/nashabanov/conformly/actions/workflows/ci.yaml/badge.svg)](https://github.com/nashabanov/conformly/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/github/nashabanov/conformly/graph/badge.svg?branch=main)](https://codecov.io/github/nashabanov/conformly)
[![PyPI](https://img.shields.io/pypi/v/conformly.svg)](https://pypi.org/project/conformly/)
[![Python Versions](https://img.shields.io/pypi/pyversions/conformly.svg)](https://pypi.org/project/conformly/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Declarative test data generator for Python.**

Define constraints once in type annotations — generate both valid and minimal invalid test data automatically.
No factories, no hardcoded fixtures, no drift when schema changes.

Conformly turns typed schemas into dictionaries for fixtures and validation tests.
Use the same schema for happy-path payloads and targeted negative cases.

## Key capabilities

- **Constraint-driven generation** from type annotations and model metadata.
- **Minimal invalid cases** targeting one field and a selected violation.
- **Schema as the single source of truth** for test data.
- Dataclasses and TypedDicts, with optional Pydantic and attrs integrations.
- Nested models, collections, reproducible seeds, and field overrides.

## Installation

Requires Python 3.12 or newer.

```bash
pip install conformly
# Optional integrations:
pip install 'conformly[pydantic]'
pip install 'conformly[attrs]'
```

## Quickstart

```python
from dataclasses import dataclass
from typing import Annotated

from conformly import GreaterOrEqual, MaxLength, MinLength, V, case, path


@dataclass
class CreateUser:
    username: Annotated[str, MinLength(3), MaxLength(32)]
    age: Annotated[int, GreaterOrEqual(18)]


payload = case(CreateUser)
assert 3 <= len(payload["username"]) <= 32
assert payload["age"] >= 18

invalid = case(
    CreateUser, valid=False, target=path("age").violate(V.BELOW_MIN)
)
assert invalid["age"] < 18
assert 3 <= len(invalid["username"]) <= 32
```

Results are dictionaries, not model instances. Invalid generation targets one
field; only the selected violation is guaranteed on that target. Defaults and
overrides are trusted rather than validated. See the
[invalid generation contract](https://github.com/nashabanov/conformly/blob/main/docs/strategies.md#invalid-generation-contract).

## Documentation and examples

Start with [Getting started](https://github.com/nashabanov/conformly/blob/main/docs/getting-started.md), browse the
[documentation index](https://github.com/nashabanov/conformly/blob/main/docs/README.md), or run the [examples](https://github.com/nashabanov/conformly/blob/main/examples/README.md).
The [API reference](https://github.com/nashabanov/conformly/blob/main/docs/api-reference.md) lists parameters and defaults.

## Development and contributing

See [CONTRIBUTING.md](https://github.com/nashabanov/conformly/blob/main/CONTRIBUTING.md) for setup and checks, and
[CHANGELOG.md](https://github.com/nashabanov/conformly/blob/main/CHANGELOG.md) for release notes and migration guidance.

## License

MIT — see [LICENSE](https://github.com/nashabanov/conformly/blob/main/LICENSE).
