"""Generate constrained dataclass payloads. Requires only conformly."""

from dataclasses import dataclass
from typing import Annotated

from conformly import GreaterOrEqual, MaxLength, MinLength, case, cases


@dataclass
class CreateUser:
    username: Annotated[str, MinLength(3), MaxLength(32)]
    age: Annotated[int, GreaterOrEqual(18)]


payload = case(CreateUser)
assert 3 <= len(payload["username"]) <= 32
assert payload["age"] >= 18


batch = cases(CreateUser, count=5)
assert len(batch) == 5
assert all(3 <= len(p["username"]) <= 32 and p["age"] >= 18 for p in batch)
print(payload)
