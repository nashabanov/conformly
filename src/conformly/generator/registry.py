from ..types import FieldKind
from .protocol import TypeGeneratorProtocol
from .types import boolean, float, integer, string

_GENERATORS: dict[FieldKind, TypeGeneratorProtocol] = {
    FieldKind.STRING: string,
    FieldKind.BOOLEAN: boolean,
    FieldKind.FLOAT: float,
    FieldKind.INTEGER: integer,
}


def get_generator(kind: FieldKind) -> TypeGeneratorProtocol:
    try:
        return _GENERATORS[kind]
    except KeyError:
        raise TypeError(f"No generators found for {kind}")
