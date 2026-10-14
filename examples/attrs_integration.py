"""Requires pip install 'conformly[attrs]'; native validators are not extracted."""

from typing import Annotated

import attrs

from conformly import GreaterOrEqual, MinLength, V, case, path


@attrs.define
class Product:
    name: Annotated[str, MinLength(3)]
    quantity: Annotated[int, GreaterOrEqual(1)]
    currency: str = "USD"


payload = case(Product)
assert len(payload["name"]) >= 3
assert payload["quantity"] >= 1
assert payload["currency"] == "USD"
invalid = case(Product, valid=False, target=path("quantity").violate(V.BELOW_MIN))
assert invalid["quantity"] < 1
assert len(invalid["name"]) >= 3
print(payload)
