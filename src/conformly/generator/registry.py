from ..types import FieldKind
from .protocol import TypeGeneratorProtocol
from .types import boolean, enum, float, integer, string

_GENERATORS: dict[FieldKind, TypeGeneratorProtocol] = {
    FieldKind.STRING: string,
    FieldKind.BOOLEAN: boolean,
    FieldKind.FLOAT: float,
    FieldKind.INTEGER: integer,
    FieldKind.ENUM: enum,
}

_MISMATCH_MAPPING: dict[FieldKind, FieldKind] = {
    FieldKind.STRING: FieldKind.INTEGER,
    FieldKind.BOOLEAN: FieldKind.STRING,
    FieldKind.INTEGER: FieldKind.STRING,
    FieldKind.FLOAT: FieldKind.STRING,
    FieldKind.ENUM: FieldKind.FLOAT,
    FieldKind.OBJECT: FieldKind.ENUM,
    FieldKind.EMAIL: FieldKind.INTEGER,
}


def get_generator(kind: FieldKind) -> TypeGeneratorProtocol:
    try:
        return _GENERATORS[kind]
    except KeyError:
        raise TypeError(f"No generators found for {kind}")


def choose_mismatch_kind(kind: FieldKind) -> FieldKind:
    return _MISMATCH_MAPPING[kind]
