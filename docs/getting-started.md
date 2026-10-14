# Getting started

## Install

Use Python 3.12 or newer. Core runtime depends only on `rstr`; dataclasses and
TypedDict need no extras.

```bash
pip install conformly
pip install 'conformly[pydantic]'  # Pydantic 2 and email-validator
pip install 'conformly[attrs]'     # attrs
pip install 'conformly[all]'       # Both optional integrations
```

## Define a schema

```python
from dataclasses import dataclass
from typing import Annotated

from conformly import GreaterOrEqual, MaxLength, MinLength, V, case, cases, path


@dataclass
class CreateUser:
    username: Annotated[str, MinLength(3), MaxLength(32)]
    age: Annotated[int, GreaterOrEqual(18)]
```

Constraints describe the input your application accepts. Dataclasses themselves
do not validate these constraints; your application still owns validation.

## Generate valid data

```python
payload = case(CreateUser)
assert 3 <= len(payload["username"]) <= 32
assert payload["age"] >= 18
payloads = cases(CreateUser, count=10)
assert len(payloads) == 10
```

## Generate a negative case

```python
invalid = case(
    CreateUser, valid=False, target=path("age").violate(V.BELOW_MIN)
)
assert invalid["age"] < 18
assert 3 <= len(invalid["username"]) <= 32
```

A negative case targets one field. Other generated fields remain valid;
other constraints on the selected target need not remain satisfied.
[Strategies](strategies.md) explains selection and enumeration.

## Use payloads in tests

The following test body assumes your application's `client` fixture and the
`CreateUser` schema above. Match status codes to your API's validation contract.

```python
def test_create_user(client):
    payload = case(CreateUser)
    response = client.post("/users", json=payload)
    assert response.status_code == 201


def test_reject_invalid_user(client):
    invalid_payloads = cases(CreateUser, valid=False, strategy="all")
    for payload in invalid_payloads:
        response = client.post("/users", json=payload)
        assert response.status_code == 400
```

`"all"` generates one negative case per eligible field, not every violation.
Use `"all_violations"` to enumerate available violations.
For a standalone validator with positive and negative tests, run
[pytest_integration.py](../examples/pytest_integration.py).

Next: [Generation](generation.md) · [Integrations](integrations.md)
