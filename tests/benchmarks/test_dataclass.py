from .models import DataclassUser
import pytest

from conformly import case, cases
from conformly.parsing.adapters.dataclass import parse
from conformly.resolver.resolve import resolve_model


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
