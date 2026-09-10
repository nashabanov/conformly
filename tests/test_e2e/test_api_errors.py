from _models import User
import pytest

from conformly import (
    case,
    cases,
)
from conformly.exceptions import GenerationError


class TestApiErrors:
    def test_case_raises_if_strategy_all(self) -> None:
        with pytest.raises(GenerationError):
            case(User, valid=False, strategy="all")

    def test_raises_if_valid_and_not_default_strategy(self) -> None:
        with pytest.raises(GenerationError):
            case(User, valid=True, strategy="random")

        with pytest.raises(GenerationError):
            cases(User, valid=True, strategy="random")

    def test_raises_if_valid_and_type_mismatch_allowed(self) -> None:
        with pytest.raises(GenerationError):
            case(User, allow_type_mismatch=True)

        with pytest.raises(GenerationError):
            cases(User, allow_type_mismatch=True)

    @pytest.mark.parametrize("strategy", ["random", "first", "name"])
    def test_raises_if_strategy_not_all_and_structural_allowed(
        self, strategy: str
    ) -> None:
        with pytest.raises(GenerationError):
            cases(
                User, valid=False, strategy=strategy, allow_structural_violations=True
            )

    def test_raises_if_valid_and_structural_allowed(self) -> None:
        with pytest.raises(GenerationError):
            cases(User, allow_structural_violations=True)

    def test_raises_if_count_less_than_one(self) -> None:
        with pytest.raises(GenerationError):
            cases(User, count=0)
