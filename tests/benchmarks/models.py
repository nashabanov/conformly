from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel

from conformly.constraints import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    MaxLength,
    MinLength,
    Pattern,
)


@dataclass
class DataclassAddress:
    street: Annotated[str, MinLength(5), MaxLength(50)]
    city: Annotated[str, MinLength(5), MaxLength(50)]
    country: Literal["Geramny", "Russia", "China", "USA"]


@dataclass
class DataclassProfile:
    bio: Annotated[str | None, MaxLength(300)]
    rating: Annotated[float, GreaterThan(0.0), LessOrEqual(100.0)]
    role: Literal["admin", "moderator", "user", "guest"]


@dataclass
class DataclassUser:
    id: int
    username: Annotated[str, MinLength(3), MaxLength(25)]
    email: Annotated[str, Pattern(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")]
    phone: Annotated[str, Pattern(r"^\+?[1-9]\d{1,14}$")]
    age: Annotated[int, GreaterOrEqual(18), LessOrEqual(120)]
    address: DataclassAddress
    profile: DataclassProfile
    is_active: bool = True


class PydanticAddress(BaseModel):
    pass


class PydanticProfile(BaseModel):
    pass


class PydanticUser(BaseModel):
    pass
