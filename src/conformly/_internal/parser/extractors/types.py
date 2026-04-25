from enum import Enum
from types import UnionType
from typing import (
    Annotated,
    Any,
    Literal,
    TypedDict,
    Union,
    get_args,
    get_origin,
)

from conformly._internal.constraints import Constraint, OneOf, UniqueItems
from conformly._internal.types import ENUMERATED_TYPE
from conformly.exceptions import SchemaError

UNION_TYPES = (Union, UnionType)


def extract_runtime_type_and_constraints(
    field_type: Any, field_name: str
) -> tuple[type, tuple[Constraint, ...]]:
    t = field_type
    outer_constraints: tuple[Constraint, ...] = ()

    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    if get_origin(t) in UNION_TYPES:
        args = get_args(t)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) >= 2:
            t = args[0]
        else:
            raise SchemaError(
                f"Field '{field_name}': unsupported union type",
                context={
                    "code": "unsupported_union",
                    "field_name": field_name,
                    "field_type": repr(field_type),
                    "allowed": "Optional[T], Union[T, None]",
                },
            )

    if get_origin(t) is Literal:
        values = get_args(t)
        if not values:
            raise SchemaError(
                f"Field '{field_name}': empty Literal",
                context={
                    "code": "empty_literal",
                    "field_name": field_name,
                    "field_type": repr(field_type),
                },
            )
        return ENUMERATED_TYPE, (OneOf(values),)

    if isinstance(t, type) and issubclass(t, Enum):
        members = list(t)
        if not members:
            raise SchemaError(
                f"Field '{field_name}': empty Enum",
                context={
                    "code": "empty_enum",
                    "field_name": field_name,
                    "field_type": t.__name__,
                },
            )
        values = tuple(member.value for member in members)
        return ENUMERATED_TYPE, (OneOf(values),)

    if isinstance(t, type):
        if is_special_string_type(t):
            return t, outer_constraints

        return t, outer_constraints

    raise SchemaError(
        f"Field '{field_name}': unsupported type annotation",
        context={
            "code": "unsupported_type",
            "field_name": field_name,
            "field_type": repr(field_type),
        },
    )


class ListParts(TypedDict):
    item: Any


class DictParts(TypedDict):
    key: Any
    value: Any


class ListContainer(TypedDict):
    kind: Literal["list"]
    origin: type
    parts: ListParts
    constraints: tuple[Constraint, ...]


class DictContainer(TypedDict):
    kind: Literal["dict"]
    origin: type
    parts: DictParts
    constraints: tuple[Constraint, ...]


class NoContainer(TypedDict):
    kind: Literal["scalar"]


ContainerSpec = ListContainer | DictContainer | NoContainer


def extract_container(field_type: Any, field_name: str) -> ContainerSpec:
    t = field_type

    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    origin = get_origin(t)

    if origin is None:
        return {"kind": "scalar"}

    args = get_args(t)

    if origin in (list, set, frozenset):
        if not args:
            raise SchemaError(
                f"Field '{field_name}': empty collection",
                context={
                    "code": "empty_collection",
                    "field_name": field_name,
                    "field_type": repr(field_type),
                },
            )
        instrinsic_constraints = (
            (UniqueItems(True),) if origin in (set, frozenset) else ()
        )
        return {
            "kind": "list",
            "origin": origin,
            "parts": {"item": args[0]},
            "constraints": instrinsic_constraints,
        }

    if origin is dict:
        if len(args) != 2:
            raise SchemaError(
                f"Field '{field_name}': dict must have 2 type args",
                context={
                    "code": "wrong_dict_type_args",
                    "field_name": field_name,
                    "field_type": repr(field_type),
                },
            )
        return {
            "kind": "dict",
            "origin": dict,
            "parts": {"key": args[0], "value": args[1]},
            "constraints": (),
        }

    return {"kind": "scalar"}


def is_nullable(field_type: Any) -> bool:
    t = field_type
    if get_origin(t) is Annotated:
        t = get_args(t)[0]

    return type(None) in get_args(t)


def is_special_string_type(t: type) -> bool:
    try:
        from ...fields import SpecialString

        return isinstance(t, type) and issubclass(t, SpecialString)
    except ImportError:
        return False
