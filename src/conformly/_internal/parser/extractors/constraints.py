from collections.abc import Mapping
from typing import Annotated, Any, cast, get_args, get_origin

from conformly._internal.constraints import (
    ALLOWED_CONSTRAINT_TYPE,
    COLLECTION_CONSTRAINTS,
    NUMERIC_CONSTRAINTS,
    STRING_CONSTRAINTS,
    Constraint,
    ConstraintType,
    MaxItems,
    MinItems,
    OneOf,
    UniqueItems,
    create_constraint,
)
from conformly.exceptions import SchemaError

_COLLECTION_CONTRAINTS_TYPE = (MinItems, MaxItems, UniqueItems)


def is_constraints_consistent(constraints: tuple[Constraint, ...]) -> bool:
    has_one_of = any(isinstance(c, OneOf) for c in constraints)
    return not has_one_of or len(constraints) == 1


def split_collection_constraints(
    constraints: tuple[Constraint, ...],
) -> tuple[tuple[Constraint, ...], tuple[Constraint, ...]]:
    collection_constraints = []
    element_constraints = []

    for c in constraints:
        if isinstance(c, _COLLECTION_CONTRAINTS_TYPE):
            collection_constraints.append(c)
        else:
            element_constraints.append(c)

    return tuple(element_constraints), tuple(collection_constraints)


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

    if k == "unique_items":
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes")
        if isinstance(v, (int, float)):
            return bool(v)
        raise SchemaError(
            f"Constraint '{k}' expects boolean value",
            context={
                "code": "invalid_constraint_value",
                "constraint_type": k,
                "value": v,
                "expected": bool,
                "actual": type(v).__name__,
            },
        )

    if k in STRING_CONSTRAINTS:
        if isinstance(v, int) and not isinstance(v, bool):
            return v
        if isinstance(v, str):
            try:
                return int(v.strip())
            except ValueError as e:
                raise SchemaError(
                    f"Constraint '{k}' expects integer value",
                    context={
                        "code": "invalid_constraint_value",
                        "constraint_type": k,
                        "value": v,
                        "expected": int,
                    },
                ) from e
        raise SchemaError(
            f"Constraint '{k}' expects integer value",
            context={
                "code": "invalid_constraint_value",
                "constraint_type": k,
                "value": v,
                "expected": int,
                "actual": type(v).__name__,
            },
        )

    if k in NUMERIC_CONSTRAINTS:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        if isinstance(v, str):
            s = v.strip()
            try:
                return (
                    int(s) if all(ch.isdigit() for ch in s.lstrip("+-")) else float(s)
                )
            except ValueError as e:
                raise SchemaError(
                    f"Constraint '{k}' expects numeric value",
                    context={
                        "code": "invalid_constraint_value",
                        "constraint_type": k,
                        "value": v,
                        "expected": "number",
                    },
                ) from e
        raise SchemaError(
            f"Constraint '{k}' expects numeric value",
            context={
                "code": "invalid_constraint_value",
                "constraint_type": k,
                "value": v,
                "expected": "number",
                "actual": type(v).__name__,
            },
        )

    if k in COLLECTION_CONSTRAINTS:
        if k in ("min_items", "max_items"):
            if isinstance(v, int) and not isinstance(v, bool):
                return v
            if isinstance(v, str):
                try:
                    return int(v.strip())
                except ValueError as e:
                    raise SchemaError(
                        f"Constraint '{k}' expects numeric value",
                        context={
                            "code": "invalid_constraint_value",
                            "constraint_type": k,
                            "value": v,
                            "expected": "number",
                        },
                    ) from e
        raise SchemaError(
            f"Constraint '{k}' expects numeric value",
            context={
                "code": "invalid_constraint_value",
                "constraint_type": k,
                "value": v,
                "expected": "number",
                "actual": type(v).__name__,
            },
        )


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
        raise SchemaError(
            f"Unknown constraint type {k}",
            context={
                "code": "unknown_constraint_type",
                "constraint_type": k,
                "allowed": sorted(ALLOWED_CONSTRAINT_TYPE),
            },
        )
    return cast("ConstraintType", k)
