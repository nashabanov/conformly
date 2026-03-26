from dataclasses import dataclass

from ...types import FieldKind, LengthRange


@dataclass(frozen=True)
class StringSemantic:
    kind: FieldKind
    length_range: LengthRange
    pattern: str | None
    has_constraints: bool

    def __post_init__(self) -> None:
        _ALLOWED_KINDS = {FieldKind.STRING, FieldKind.EMAIL}
        if self.kind not in _ALLOWED_KINDS:
            raise ValueError(
                f"StringSemantic does not support kind: {self.kind}. "
                f"Allowed: {_ALLOWED_KINDS}"
            )
