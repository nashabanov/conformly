from .models import PydanticUser
import pytest

from conformly import case, cases
from conformly.parsing.adapters.pydantic import parse
from conformly.resolver.resolve import resolve_model


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
