from dataclasses import dataclass
from typing import Any

from .base import Constraint


@dataclass(frozen=True)
class OneOf(Constraint):
    values: tuple[Any, ...]
