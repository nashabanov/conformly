from conformly._internal.types import FieldKind
from conformly.exceptions import ResolutionError

_ALLOWED_STRING_KINDS = {
    FieldKind.STRING,
    FieldKind.EMAIL,
    FieldKind.IPv4,
    FieldKind.IPv6,
    FieldKind.IPvAny,
    FieldKind.URL,
    FieldKind.HTTPURL,
}


def validate_string_kind(kind: FieldKind) -> None:
    if kind not in _ALLOWED_STRING_KINDS:
        raise ResolutionError(
            f"StringSemantic does not support kind: {kind}",
            context={
                "code": "unsupported_string_kind",
                "kind": kind.value,
                "allowed": [k.value for k in _ALLOWED_STRING_KINDS],
            },
        )
