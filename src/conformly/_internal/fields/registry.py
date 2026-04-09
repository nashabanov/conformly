from dataclasses import dataclass

from ...types import FieldKind
from .special_types import Email, IPv4, IPv6, IPvAny, SpecialString


@dataclass(frozen=True)
class SpecialStringSpec:
    kind: FieldKind
    conformly_type: type[SpecialString]
    pydantic_name: str


SPECIAL_STRINGS: tuple[SpecialStringSpec, ...] = (
    SpecialStringSpec(FieldKind.EMAIL, Email, "EmailStr"),
    SpecialStringSpec(FieldKind.IPv4, IPv4, "IPv4Address"),
    SpecialStringSpec(FieldKind.IPv6, IPv6, "IPv6Address"),
    SpecialStringSpec(FieldKind.IPvAny, IPvAny, "IPvAnyAddress"),
)


SPECIAL_KINDS: set[FieldKind] = {spec.kind for spec in SPECIAL_STRINGS}

SPECIAL_TYPE_TO_KIND: dict[type[SpecialString], FieldKind] = {
    spec.conformly_type: spec.kind for spec in SPECIAL_STRINGS
}

SPECIAL_NAME_TO_TYPE: dict[str, type[SpecialString]] = {
    spec.pydantic_name: spec.conformly_type for spec in SPECIAL_STRINGS
}
