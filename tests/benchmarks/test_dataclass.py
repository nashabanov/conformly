from dataclasses import dataclass
from typing import Annotated, Literal

import pytest

from conformly import case, cases
from conformly._internal.constraints import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    MaxLength,
    MinLength,
    Pattern,
)
from conformly._internal.parsing.adapters.dataclass import parse
from conformly.resolver.resolve import resolve_model


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


@pytest.mark.benchmark
def test_dataclass_parse_only(benchmark) -> None:
    benchmark(lambda: parse(DataclassUser))


@pytest.mark.benchmark
def test_dataclass_resolving_only(benchmark) -> None:
    parsed_model = parse(DataclassUser)
    benchmark(lambda: resolve_model(parsed_model))


@pytest.mark.benchmark
def test_dataclass_cold_single(benchmark) -> None:
    benchmark(lambda: case(DataclassUser, valid=True))


@pytest.mark.benchmark
def test_dataclass_warm_single(benchmark) -> None:
    case(DataclassUser, valid=True)

    benchmark(lambda: case(DataclassUser, valid=True))


@pytest.mark.benchmark
def test_dataclass_batch_100(benchmark) -> None:
    benchmark(lambda: cases(DataclassUser, valid=True, count=100))


@pytest.mark.benchmark
def test_dataclass_batch_1000(benchmark) -> None:
    benchmark(lambda: cases(DataclassUser, valid=True, count=1000))


@pytest.mark.benchmark
def test_dataclass_invalid_all(benchmark) -> None:
    benchmark(lambda: cases(DataclassUser, valid=False, strategy="all"))


@pytest.mark.benchmark
def test_dataclass_invalid_all_structural(benchmark) -> None:
    benchmark(
        lambda: cases(
            DataclassUser, valid=False, strategy="all", allow_structural_violations=True
        )
    )
