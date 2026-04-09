import pytest

pytest.importorskip("pydantic", reason="Pydantic adapter requires 'pydantic' package")
from typing import Literal

from pydantic import BaseModel, Field

from conformly import case, cases
from conformly._internal.parsing.adapters.pydantic import parse
from conformly.resolver.resolve import resolve_model


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


@pytest.mark.benchmark
def test_pydantic_parse_only(benchmark) -> None:
    benchmark(lambda: parse(PydanticUser))


@pytest.mark.benchmark
def test_pydantic_resolving_only(benchmark) -> None:
    parsed_model = parse(PydanticUser)
    benchmark(lambda: resolve_model(parsed_model))


@pytest.mark.benchmark
def test_pydantic_cold_single(benchmark) -> None:
    benchmark(lambda: case(PydanticUser, valid=True))


@pytest.mark.benchmark
def test_pydantic_warm_single(benchmark) -> None:
    case(PydanticUser, valid=True)

    benchmark(lambda: case(PydanticUser, valid=True))


@pytest.mark.benchmark
def test_pydantic_batch_100(benchmark) -> None:
    benchmark(lambda: cases(PydanticUser, valid=True, count=100))


@pytest.mark.benchmark
def test_pydantic_batch_1000(benchmark) -> None:
    benchmark(lambda: cases(PydanticUser, valid=True, count=1000))


@pytest.mark.benchmark
def test_pydantic_invalid_all(benchmark) -> None:
    benchmark(lambda: cases(PydanticUser, valid=False, strategy="all"))


@pytest.mark.benchmark
def test_pydantic_invalid_all_structural(benchmark) -> None:
    benchmark(
        lambda: cases(
            PydanticUser, valid=False, strategy="all", allow_structural_violations=True
        )
    )
