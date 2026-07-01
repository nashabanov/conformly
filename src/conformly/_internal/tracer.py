from dataclasses import dataclass
from enum import Enum
from typing import Any

from conformly._internal.constraints import ConstraintType
from conformly._internal.types import ViolationType


class ValueSource(Enum):
    GENERATED = "generated"
    MODEL_DEFAULT = "model_default"
    OVERRIDDEN = "overridden"


@dataclass(frozen=True, slots=True)
class Trace:
    target_path: str
    seed: int | None

    constraint: ConstraintType | None
    violation: ViolationType | None

    generated_value: Any
    value_source: ValueSource


class Tracer:
    _target_path: str = ""
    _seed: int | None

    _constraint: ConstraintType | None
    _violation: ViolationType | None

    _generated_value: Any
    _value_source: ValueSource

    def __init__(self) -> None:
        self._target_path = ""
        self._seed = None
        self._constraint = None
        self._violation = None
        self._generated_value = None
        self._value_source = ValueSource.GENERATED

    def record_plan(
        self,
        target_path: str,
        constraint: ConstraintType | None = None,
        violation: ViolationType | None = None,
    ) -> None:
        self._target_path = target_path
        self._constraint = constraint
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
            constraint=self._constraint,
            violation=self._violation,
            generated_value=self._generated_value,
            value_source=self._value_source,
        )
