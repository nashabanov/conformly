from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, Field

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
    country: Literal["Germany", "Russia", "China", "USA"]


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
    street: str = Field(..., min_length=5, max_length=50)
    city: str = Field(..., min_length=5, max_length=50)
    country: Literal["Germany", "Russia", "China", "USA"]


class PydanticProfile(BaseModel):
    bio: str | None = Field(None, max_length=300)
    rating: float = Field(..., gt=0.0, le=100.0)
    role: Literal["admin", "moderator", "user", "guest"]


class PydanticUser(BaseModel):
    id: int
    username: str = Field(..., min_length=3, max_length=25)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    age: int = Field(..., ge=18, le=120)
    address: PydanticAddress
    profile: PydanticProfile
    is_active: bool = True
