# Model integrations

All integrations return dictionaries, including nested models. Validation,
converters, constructors, and business rules are not executed. Adapters register
automatically when their optional packages are installed; importing `conformly`
does not require Pydantic or attrs.

## Dataclasses (built in)

Use `Annotated` or `dataclasses.field(metadata=...)` for constraints. Defaults
and default factories are supported; see [their priority](generation.md#optional-fields-and-defaults).
Run [basic_generation.py](../examples/basic_generation.py).

## TypedDict (built in)

```python
from typing import Annotated, NotRequired, TypedDict

from conformly import MinLength, case


class Request(TypedDict):
    name: Annotated[str, MinLength(3)]
    comment: NotRequired[str]


payload = case(Request)
assert len(payload["name"]) >= 3
assert isinstance(payload["comment"], str)
```

`Required`, `NotRequired`, and `total=False` control requiredness. Valid
generation currently includes optional keys. Requiredness is separate from
nullability; `NotRequired[int]` does not mean `int | None`.

## Pydantic 2

Install `pip install 'conformly[pydantic]'`. The extra includes Pydantic 2
and email-validator. Supported `Field` constraints map to Conformly constraints:
`gt`, `ge`, `lt`, `le`, `multiple_of`, `min_length`, `max_length`, and `pattern`.
For lists, sets, and frozensets, `Field` lengths map to item counts. Prefer
Conformly `MinItems`/`MaxItems` in `Annotated` for tuples and dictionaries.

```python
from pydantic import BaseModel, Field

from conformly import case


class User(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    age: int = Field(ge=18)


payload = case(User)
User.model_validate(payload)
```

Pydantic `EmailStr`, `IPv4Address`, `IPv6Address`, `IPvAnyAddress`, `AnyUrl`, and
`HttpUrl` map to format generators. `constr()`, `conint()`, and functional
validators are not interpreted as generation constraints; use `Field()`.
Aliases and custom validation rules may require separate application handling.
An extra-field violation is offered only when `extra="forbid"`.

Run [pydantic_integration.py](../examples/pydantic_integration.py) for positive
validation and targeted rejection with `ValidationError`.

## attrs

Install `pip install 'conformly[attrs]'`. Use `Annotated` constraints:

```python
from typing import Annotated

import attrs

from conformly import GreaterOrEqual, case


@attrs.define
class Quantity:
    value: Annotated[int, GreaterOrEqual(1)]


assert case(Quantity)["value"] >= 1
```

Native attrs validators and converters are not interpreted. Defaults and
factories are supported, except factories requiring `self`.
Run [attrs_integration.py](../examples/attrs_integration.py).

## Mixed and nested models

Supported model kinds can be nested across adapters, including a TypedDict
inside a dataclass and a dataclass inside Pydantic. Each nested type uses its
own declaration rules. Optional dependencies are needed for every optional
adapter used in the schema. Cyclic references are unsupported.

[Generation](generation.md) · [Constraints](constraints.md)
