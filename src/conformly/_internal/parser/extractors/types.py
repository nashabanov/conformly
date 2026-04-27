from dataclasses import dataclass
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

from .constraints import parse_annotated_constraints

from conformly._internal.constraints import Constraint, OneOf, UniqueItems
from conformly._internal.types import ENUMERATED_TYPE
from conformly.exceptions import SchemaError

UNION_TYPES = (Union, UnionType)


@dataclass(frozen=True, slots=True)
class ScalarNode:
    kind: Literal["scalar"]
    runtime_type: Any
    nullable: bool
    constraints: tuple[Constraint, ...]


@dataclass(frozen=True, slots=True)
class ListNode:
    kind: Literal["list"]
    runtime_type: Any
    origin: type
    nullable: bool
    constraints: tuple[Constraint, ...]
    item: "TypeNode"


@dataclass(frozen=True, slots=True)
class DictNode:
    kind: Literal["dict"]
    runtime_type: Any
    nullable: bool
    constraints: tuple[Constraint, ...]
    key: "TypeNode"
    value: "TypeNode"


TypeNode = ScalarNode | ListNode | DictNode


def normalize_type(field_type: Any, field_name: str) -> TypeNode:
    t, annotated_constraints = _unwrap_annotated(field_type)
    t, nullable = _unwrap_optional(t, field_name)
    return _build_node(t, field_name, nullable, annotated_constraints)


def _unwrap_annotated(t: Any) -> tuple[Any, tuple[Constraint, ...]]:
    if get_origin(t) is Annotated:
        return get_args(t)[0], parse_annotated_constraints(t)
    return t, ()


def _unwrap_optional(t: Any, field_name: str) -> tuple[Any, bool]:
    origin = get_origin(t)
    args = get_args(t)

    if origin in UNION_TYPES:
        non_none = [a for a in args if a is not type(None)]

        if len(non_none) == 1 and len(args) >= 2:
            return non_none[0], True

        raise SchemaError(
            f"Field '{field_name}': unsupported union type",
            context={
                "code": "unsupported_union",
                "field_name": field_name,
                "field_type": repr(t),
            },
        )

    return t, False


def _build_node(
    t: Any,
    field_name: str,
    nullable: bool,
    constraints: tuple[Constraint, ...],
) -> TypeNode:
    origin = get_origin(t)
    args = get_args(t)

    if origin in (list, set, frozenset):
        if not args:
            raise SchemaError(
                f"Field '{field_name}': '{origin.__name__}' must be parameterized",
                context={
                    "code": "empty_collection",
                    "field_name": field_name,
                    "field_type": repr(t),
                },
            )
        item = normalize_type(args[0], field_name)
        intrinsic: tuple[Constraint, ...] = (
            (UniqueItems(True),) if origin in (set, frozenset) else ()
        )
        return ListNode(
            kind="list",
            runtime_type=origin,
            origin=origin,
            nullable=nullable,
            constraints=(*constraints, *intrinsic),
            item=item,
        )

    if origin is dict:
        if len(args) != 2:
            raise SchemaError(
                f"Field '{field_name}': 'dict' requires exactly 2 type arguments",
                context={
                    "code": "wrong_dict_type_args",
                    "field_name": field_name,
                    "field_type": repr(t),
                },
            )
        return DictNode(
            kind="dict",
            runtime_type=dict,
            nullable=nullable,
            constraints=constraints,
            key=normalize_type(args[0], field_name),
            value=normalize_type(args[1], field_name),
        )

    if origin is Literal:
        if not args:
            raise SchemaError(
                f"Field '{field_name}': 'Literal' must contain at least one value",
                context={
                    "code": "empty_literal",
                    "field_name": field_name,
                    "field_type": repr(t),
                },
            )
        return ScalarNode(
            kind="scalar",
            runtime_type=ENUMERATED_TYPE,
            nullable=nullable,
            constraints=(*constraints, OneOf(args)),
        )

    if isinstance(t, type) and issubclass(t, Enum):
        values = tuple(member.value for member in t)
        return ScalarNode(
            kind="scalar",
            runtime_type=ENUMERATED_TYPE,
            nullable=nullable,
            constraints=(*constraints, OneOf(values)),
        )

    if isinstance(t, type):
        return ScalarNode(
            kind="scalar",
            runtime_type=t,
            nullable=nullable,
            constraints=constraints,
        )

    raise SchemaError(
        f"Field '{field_name}': unsupported type annotation '{t!r}'",
        context={
            "code": "unsupported_type",
            "field_name": field_name,
            "field_type": repr(t),
        },
    )
