from dataclasses import dataclass, field
from typing import Any, Literal

ConstraintType = Literal["min", "max", "pattern", "length"]
_UNSET = object()


@dataclass(frozen=True)
class ConstraintSpec:
    constraint_type: ConstraintType
    value: Any

    def __repr__(self) -> str:
        return f"Constraint({self.constraint_type}={self.value!r})"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: type
    constraints: list[ConstraintSpec] = field(default_factory=list)
    default: Any = _UNSET
    nullable: bool = False

    def get_constraint(self, constraint_type: ConstraintType) -> ConstraintSpec | None:
        for c in self.constraints:
            if c.constraint_type == constraint_type:
                return c
        return None

    def has_default(self) -> bool:
        return self.default is not _UNSET

    def is_optional(self) -> bool:
        return self.nullable or self.has_default()

    def __repr__(self) -> str:
        return (
            f"Field(name={self.name!r}, "
            f"type={self.type!r}, "
            f"constraints={[repr(c) for c in self.constraints]!r})"
        )
