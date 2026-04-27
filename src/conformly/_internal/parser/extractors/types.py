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
    origin = get_origin(t)

    if origin in (list, set, frozenset):
        args = get_args(t)
        if not args:
            raise SchemaError(
                f"Field '{field_name}': empty collection",
                context={
                    "code": "empty_collection",
                    "field_name": field_name,
                    "field_type": repr(field_type),
                },
            )

        item_node = normalize_type(args[0], field_name)

        intrinsic_constraints = (
            (UniqueItems(True),) if origin in (set, frozenset) else ()
        )

        return ListNode(
            kind="list",
            runtime_type=origin,
            origin=origin,
            nullable=nullable,
            constraints=(*annotated_constraints, *intrinsic_constraints),
            item=item_node,
        )

    if origin is dict:
        args = get_args(t)
        if len(args) != 2:
            raise SchemaError(
                f"Field '{field_name}': dict must have 2 type args",
                context={
                    "code": "wrong_dict_type_args",
                    "field_name": field_name,
                    "field_type": repr(field_type),
                },
            )

        key_node = normalize_type(args[0], field_name)
        value_node = normalize_type(args[1], field_name)

        return DictNode(
            kind="dict",
            runtime_type=dict,
            nullable=nullable,
            constraints=annotated_constraints,
            key=key_node,
            value=value_node,
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

        return ScalarNode(
            kind="scalar",
            runtime_type=ENUMERATED_TYPE,
            nullable=nullable,
            constraints=(*annotated_constraints, OneOf(values)),
        )

    if isinstance(t, type) and issubclass(t, Enum):
        values = tuple(member.value for member in t)

        return ScalarNode(
            kind="scalar",
            runtime_type=ENUMERATED_TYPE,
            nullable=nullable,
            constraints=(*annotated_constraints, OneOf(values)),
        )

    if isinstance(t, type):
        return ScalarNode(
            kind="scalar",
            runtime_type=t,
            nullable=nullable,
            constraints=annotated_constraints,
        )

    raise SchemaError(
        f"Field '{field_name}': unsupported type",
        context={
            "code": "unsupported_type",
            "field_name": field_name,
            "field_type": repr(field_type),
        },
    )


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
