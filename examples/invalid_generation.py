"""Select invalid fields and exact violations. Requires only conformly."""

from dataclasses import dataclass
from typing import Annotated

from conformly import GreaterOrEqual, MinLength, V, case, cases, path


@dataclass
class Order:
    reference: Annotated[str, MinLength(3)]
    quantity: Annotated[int, GreaterOrEqual(1)]


invalid = case(Order, valid=False, strategy="quantity")
assert invalid["quantity"] < 1
assert len(invalid["reference"]) >= 3
short = case(
    Order, valid=False, strategy=path(Order, lambda o: o.reference).violate(V.TOO_SHORT)
)
assert len(short["reference"]) < 3
assert short["quantity"] >= 1
all_fields = cases(Order, valid=False, strategy="all")
assert len(all_fields) == 2
for payload in all_fields:
    assert (len(payload["reference"]) < 3) != (payload["quantity"] < 1)
print(short)
