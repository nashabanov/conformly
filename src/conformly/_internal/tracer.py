from dataclasses import dataclass
from enum import Enum
from typing import Any

from conformly._internal.constraints.base import Constraint
from conformly._internal.fields import SpecialString
from conformly._internal.types import ViolationType


class ValueSource(Enum):
    GENERATED = "generated"
    MODEL_DEFAULT = "model_default"
    OVERRIDDEN = "overridden"


Rule = Constraint | type[SpecialString] | None


@dataclass(frozen=True, slots=True)
class Trace:
    target_path: str
    seed: int | None

    rule: Rule
    violation: ViolationType | None

    generated_value: Any
    value_source: ValueSource


class Tracer:
    _target_path: str = ""
    _seed: int | None

    _rule: Rule
    _violation: ViolationType | None

    _generated_value: Any
    _value_source: ValueSource

    def __init__(self) -> None:
        self._target_path = ""
        self._seed = None
        self._rule = None
        self._violation = None
        self._generated_value = None
        self._value_source = ValueSource.GENERATED

    def record_plan(
        self,
        target_path: str,
        rule: Rule = None,
        violation: ViolationType | None = None,
    ) -> None:
        self._target_path = target_path
        self._rule = rule
        self._violation = violation

    def record_generation(
        self, value: Any, source: ValueSource, seed: int | None = None
    ) -> None:
        self._seed = seed
        self._generated_value = value
        self._value_source = source

    def build(self) -> Trace:
        return Trace(
            target_path=self._target_path,
            seed=self._seed,
            rule=self._rule,
            violation=self._violation,
            generated_value=self._generated_value,
            value_source=self._value_source,
        )
