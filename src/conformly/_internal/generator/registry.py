from .protocol import TypeGeneratorProtocol
from .types import (
    boolean,
    email,
    enum,
    float,
    integer,
    ipv4,
    ipv6,
    ipvany,
    list,
    string,
    url,
    uuid,
)

from conformly._internal.types import FieldKind

_GENERATORS: dict[FieldKind, TypeGeneratorProtocol] = {
    FieldKind.STRING: string,
    FieldKind.BOOLEAN: boolean,
    FieldKind.FLOAT: float,
    FieldKind.INTEGER: integer,
    FieldKind.ENUM: enum,
    FieldKind.EMAIL: email,
    FieldKind.IPv4: ipv4,
    FieldKind.IPv6: ipv6,
    FieldKind.IPvAny: ipvany,
    FieldKind.LIST: list,
    FieldKind.UUID: uuid,
    FieldKind.URL: url,
    FieldKind.HTTPURL: url,
}

_MISMATCH_MAPPING: dict[FieldKind, FieldKind] = {
    FieldKind.STRING: FieldKind.INTEGER,
    FieldKind.BOOLEAN: FieldKind.STRING,
    FieldKind.INTEGER: FieldKind.STRING,
    FieldKind.FLOAT: FieldKind.STRING,
    FieldKind.ENUM: FieldKind.FLOAT,
    FieldKind.OBJECT: FieldKind.ENUM,
    FieldKind.EMAIL: FieldKind.INTEGER,
    FieldKind.IPv4: FieldKind.INTEGER,
    FieldKind.IPv6: FieldKind.INTEGER,
    FieldKind.IPvAny: FieldKind.INTEGER,
    FieldKind.LIST: FieldKind.INTEGER,
    FieldKind.UUID: FieldKind.FLOAT,
    FieldKind.URL: FieldKind.FLOAT,
    FieldKind.HTTPURL: FieldKind.INTEGER,
}


def get_generator(kind: FieldKind) -> TypeGeneratorProtocol:
    try:
        return _GENERATORS[kind]
    except KeyError:
        raise TypeError(f"No generators found for {kind}")


def choose_mismatch_kind(kind: FieldKind) -> FieldKind:
    return _MISMATCH_MAPPING[kind]
