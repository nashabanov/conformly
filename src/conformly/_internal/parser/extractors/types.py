from enum import Enum
from types import UnionType
from typing import (
    Annotated,
    Any,
    Literal,
    Union,
    get_args,
    get_origin,
)

from ...constraints import Constraint, OneOf
from ...types import ENUMERATED_TYPE

UNION_TYPES = (Union, UnionType)
COLLECTION_ORIGINS = (list, list)


def extract_runtime_type_and_constraints(
    field_type: Any, field_name: str
) -> tuple[type, tuple[Constraint, ...], type | None]:
    t = field_type
    outer_constraints: tuple[Constraint, ...] = ()

    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    origin = get_origin(t)

    if origin in COLLECTION_ORIGINS:
        args = get_args(t)
        if not args:
            raise TypeError(f"Field '{field_name}': empty collection {field_type!r}")

        element_annotation = args[0]

        if get_origin(element_annotation) is Annotated:
            element_type = get_args(element_annotation)[0]
            element_constraints = get_args(element_annotation)[1:]
        else:
            element_type = element_annotation
            element_constraints = ()

        return element_type, element_constraints or outer_constraints, origin

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
        return ENUMERATED_TYPE, (OneOf(values),), None

    if isinstance(t, type) and issubclass(t, Enum):
        members = list(t)
        if not members:
            raise TypeError(
                f"Field '{field_name}': empty Enum {t.__name__} is not allowed. "
                "Must define at least one member."
            )
        values = tuple(member.value for member in members)
        return ENUMERATED_TYPE, (OneOf(values),), None

    if isinstance(t, type):
        if is_special_string_type(t):
            return t, outer_constraints, None

        return t, outer_constraints, None

    raise TypeError(f"Field '{field_name}': unsupported type annotation {field_type!r}")


def is_nullable(field_type: Any) -> bool:
    t = field_type

    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    origin = get_origin(t)

    if origin in UNION_TYPES:
        return type(None) in get_args(t)

    return False


def is_special_string_type(t: type) -> bool:
    try:
        from ...fields import SpecialString

        return isinstance(t, type) and issubclass(t, SpecialString)
    except ImportError:
        return False
