from dataclasses import dataclass, field
from typing import Annotated, Literal
import uuid

from conformly import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxItems,
    MaxLength,
    MinItems,
    MinLength,
    Pattern,
    UniqueItems,
)


@dataclass
class User:
    username: Annotated[str, MinLength(3)]
    full_name: Annotated[str, MinLength(2), MaxLength(100)]
    email: Annotated[
        str,
        Pattern(r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    ]
    bio: Annotated[str, MaxLength(500)]
    role: Literal["admin", "guest", "user"]
    is_blocked: bool


@dataclass
class TupleModel:
    fixed: tuple[Annotated[str, MinLength(2)], int]
    variadic: Annotated[tuple[str, ...], MinItems(2)]


@dataclass
class BlogPost:
    title: Annotated[str, "min_length=5", "max_length=200"]
    slug: Annotated[str, "pattern=^[a-z0-9-]+$"]
    content: Annotated[str, "min_length=10"]
    views: Annotated[int, "ge=0"]
    rating: Annotated[float, "ge=0", "le=5"]


@dataclass
class Product:
    sku: str = field(metadata={"pattern": r"^[A-Z0-9]{8}$"})
    name: str = field(metadata={"min_length": 1, "max_length": 100})
    price: float = field(metadata={"gt": 0})
    stock: int = field(metadata={"ge": 0})
    discount: float = field(metadata={"ge": 0, "le": 100, "multiple_of": 5})


@dataclass
class CreateUserRequest:
    age: Annotated[int, GreaterOrEqual(18), LessThan(120)]
    email: Annotated[str, Pattern(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
    password: Annotated[str, MinLength(8), MaxLength(128)]
    nickname: Annotated[str, MinLength(3), MaxLength(30)]


@dataclass
class OrderItem:
    product_id: Annotated[int, GreaterThan(0)]
    quantity: Annotated[int, GreaterOrEqual(1), LessOrEqual(1000)]
    unit_price: Annotated[float, GreaterThan(0)]


@dataclass
class Transaction:
    account_id: Annotated[str, Pattern(r"^ACC[0-9]{10}$")]
    amount: Annotated[float, GreaterThan(0), LessOrEqual(1_000_000)]
    description: Annotated[str, MinLength(5), MaxLength(256)]
    reference_code: Annotated[str, Pattern(r"^[A-Z0-9]{12}$")]


@dataclass
class Article:
    title: Annotated[str, MinLength(5), MaxLength(300)]
    author: str = field(metadata={"min_length": 2, "max_length": 100})
    content: Annotated[str, "min_length=50"]
    publish_date: Annotated[int, GreaterOrEqual(0)]


@dataclass
class ProductItem:
    sku: str
    price: Annotated[float, GreaterOrEqual(0)]


@dataclass
class Order:
    items: Annotated[list[ProductItem], UniqueItems(True)]
    tags: set[str]
    codes: Annotated[list[Annotated[str, MinLength(5)]], MaxItems(6)]
    flags: list[bool]


@dataclass
class UserUUID:
    id: uuid.UUID
