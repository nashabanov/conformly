from dataclasses import dataclass

from .field import ResolvedField


@dataclass(frozen=True)
class ResolvedModel:
    fields: list[ResolvedField]
