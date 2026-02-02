from enum import Enum
from types import UnionType
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from ..constraints import Constraint, OneOf
from ..types import ENUMERATED_TYPE

UNION_TYPES = (Union, UnionType)


def extract_runtime_type_and_constraints(
    field_type: Any, field_name: str
) -> tuple[type, tuple[Constraint, ...]]:
    t = field_type

    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    if get_origin(t) in UNION_TYPES:
        args = get_args(t)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) >= 2:
            t = args[0]
        else:
            raise TypeError(
                f"Field '{field_name}': unsupported union type {field_type!r}. "
                "Only Optional[T] (Union[T, None]) is allowed."
            )

    if get_origin(t) is Literal:
        values = get_args(t)
        if not values:
            raise TypeError(
                f"Field '{field_name}': empty Literal[] is not allowed. "
                "Must specify at least one value."
            )
        return ENUMERATED_TYPE, (OneOf(values),)

    if isinstance(t, type) and issubclass(t, Enum):
        members = list(t)
        if not members:
            raise TypeError(
                f"Field '{field_name}': empty Enum {t.__name__} is not allowed. "
                "Must define at least one member."
            )
        values = tuple(member.value for member in members)
        return ENUMERATED_TYPE, (OneOf(values),)

    if isinstance(t, type):
        return t, ()

    raise TypeError(f"Field '{field_name}': unsupported type annotation {field_type!r}")


def is_nullable(field_type: Any) -> bool:
    t = field_type

    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    origin = get_origin(t)

    if origin in UNION_TYPES:
        return type(None) in get_args(t)

    return False
