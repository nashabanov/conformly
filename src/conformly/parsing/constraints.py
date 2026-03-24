from collections.abc import Mapping
from typing import Annotated, Any, cast, get_args, get_origin

from ..constraints import (
    ALLOWED_CONSTRAINT_TYPE,
    NUMERIC_CONSTRAINTS,
    STRING_CONSTRAINTS,
    Constraint,
    ConstraintType,
    OneOf,
)
from ..constraints.mapping import create_constraint


def is_constraints_consistent(constraints: tuple[Constraint, ...]) -> bool:
    has_one_of = any(isinstance(c, OneOf) for c in constraints)
    return not has_one_of or len(constraints) == 1


def parse_annotated_constraints(field_type: Any) -> tuple[Constraint, ...]:
    if get_origin(field_type) is Annotated:
        args = get_args(field_type)
        metadata = args[1:]

        constraints = []
        for item in metadata:
            constraint = _metadata_to_constraints(item)
            if constraint:
                constraints.append(constraint)

        return tuple(constraints)

    return ()


def parse_metadata_constraints(metadata: Mapping[Any, Any]) -> tuple[Constraint, ...]:
    if not metadata:
        return ()

    constraints = []
    for k, v in metadata.items():
        if k.startswith("_"):
            continue

        _validate_constraint_type(k)

        constraint = create_constraint(constraint_type=k, value=v)
        constraints.append(constraint)

    return tuple(constraints)


def _coerce_constraint_value(k: ConstraintType, v: Any) -> Any:
    if k == "pattern":
        return str(v)

    if k in STRING_CONSTRAINTS:
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            s = v.strip()
            try:
                return int(s)
            except ValueError as e:
                raise ValueError(f"Constraint {k!r} expects int, got {v!r}") from e
        raise ValueError(f"Constraint {k!r} expects int, got {type(v).__name__}")

    if k in NUMERIC_CONSTRAINTS:
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            s = v.strip()
            try:
                if all(ch.isdigit() for ch in s.lstrip("+-")):
                    return int(s)
                return float(s)
            except ValueError as e:
                raise ValueError(f"Constraint {k!r} expects number, got {v!r}") from e
        raise ValueError(f"Constraint {k!r} expects number, got {type(v).__name__}")


def _metadata_to_constraints(metadata_item: Any) -> Constraint | None:
    match metadata_item:
        case Constraint():
            return metadata_item
        case str() if "=" in metadata_item:
            k, v = metadata_item.split("=", 1)
            k_validated = _validate_constraint_type(k)
            v_coerced = _coerce_constraint_value(k_validated, v)
            return create_constraint(k_validated, v_coerced)
        case str():
            k_validated = _validate_constraint_type(metadata_item)
            return create_constraint(k_validated, True)
        case {"type": k, "value": v}:
            k_validated = _validate_constraint_type(k)
            v_coerced = _coerce_constraint_value(k_validated, v)
            return create_constraint(k_validated, v_coerced)
        case _:
            return None


def _validate_constraint_type(k: str) -> ConstraintType:
    if k not in ALLOWED_CONSTRAINT_TYPE:
        raise ValueError(f"Unknown constraint type {k!r}")
    return cast("ConstraintType", k)
