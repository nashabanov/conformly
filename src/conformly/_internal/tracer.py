from dataclasses import dataclass
from enum import Enum
from typing import Any

from conformly._internal.types import ViolationType


class ValueSource(Enum):
    GENERATED = "generated"
    MODEL_DEFAULT = "model_default"
    OVERRIDDEN = "overridden"


@dataclass(frozen=True, slots=True)
class Trace:
    target_path: str
    seed: int | None

    violation: ViolationType | None

    generated_value: Any
    value_source: ValueSource


class Tracer:
    _target_path: str = ""
    _seed: int | None

    _violation: ViolationType | None

    _generated_value: Any
    _value_source: ValueSource

    def __init__(self) -> None:
        self._target_path = ""
        self._seed = None
        self._violation = None
        self._generated_value = None
        self._value_source = ValueSource.GENERATED

    def set_target_path(self, path: str) -> None:
        self._target_path = path

    def set_seed(self, seed: int | None) -> None:
        self._seed = seed

    def set_violation(self, violation: ViolationType | None) -> None:
        self._violation = violation

    def set_generated_value(self, value: Any) -> None:
        self._generated_value = value

    def set_value_source(self, source: ValueSource) -> None:
        self._value_source = source

    def build(self) -> Trace:
        return Trace(
            target_path=self._target_path,
            seed=self._seed,
            violation=self._violation,
            generated_value=self._generated_value,
            value_source=self._value_source,
        )
