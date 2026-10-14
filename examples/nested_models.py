"""Generate nested models and target a field in one list entry."""

from dataclasses import dataclass
from typing import Annotated

from conformly import GreaterOrEqual, MaxItems, MinItems, V, case, path


@dataclass
class LineItem:
    price: Annotated[int, GreaterOrEqual(1)]


@dataclass
class Order:
    items: Annotated[list[LineItem], MinItems(2), MaxItems(3)]
    customer: str


valid = case(Order)
assert 2 <= len(valid["items"]) <= 3
assert all(item["price"] >= 1 for item in valid["items"])
invalid = case(Order, valid=False, target=path("items.price").violate(V.BELOW_MIN))
assert 2 <= len(invalid["items"]) <= 3
assert sum(item["price"] < 1 for item in invalid["items"]) == 1
assert isinstance(invalid["customer"], str)
print(invalid)
