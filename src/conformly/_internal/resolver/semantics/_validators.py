from conformly._internal.types import FieldKind

_ALLOWED_STRING_KINDS = {
    FieldKind.STRING,
    FieldKind.EMAIL,
    FieldKind.IPv4,
    FieldKind.IPv6,
    FieldKind.IPvAny,
}


def validate_string_kind(kind: FieldKind) -> None:
    if kind not in _ALLOWED_STRING_KINDS:
        raise ValueError(
            f"StringSemantic does not support kind: {kind}. "
            f"Allowed: {_ALLOWED_STRING_KINDS}"
        )
