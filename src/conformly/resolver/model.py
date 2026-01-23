from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .field import ResolvedField


@dataclass(frozen=True)
class ResolvedModel:
    name: str
    fields: list[ResolvedField]
