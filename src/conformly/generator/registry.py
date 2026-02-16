import random

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


def get_generator(kind: FieldKind) -> TypeGeneratorProtocol:
    try:
        return _GENERATORS[kind]
    except KeyError:
        raise TypeError(f"No generators found for {kind}")


def choose_random_base_kind() -> FieldKind:
    return random.choice(list(_GENERATORS.keys()))


def choose_mismatch_kind(kind: FieldKind) -> FieldKind:
    mismatched_kinds = [_kind for _kind, _ in _GENERATORS.items() if _kind != kind]
    return random.choice(mismatched_kinds)
