from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin

from ...specs import FieldSpec, ModelSpec

if TYPE_CHECKING:
    from ...constraints import Constraint
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo


_PYDANTIC_TYPE_RESOLUTION: dict[str, type] = {"EmailStr": str}


def supports(model: type) -> bool:
    return hasattr(model, "__pydantic_validator__")


@lru_cache(maxsize=128)
def parse(model: type) -> ModelSpec:
    try:
        from pydantic import BaseModel
        from pydantic_core import PydanticUndefined
    except ImportError:
        raise ImportError(
            "Pydantic adapter requires 'pydantic' package. "
            "Install with: pip install 'conformly[pydantic]'"
        ) from None

    if not issubclass(model, BaseModel):
        raise TypeError(
            f"Unsupported model type: {model}. Expected Pydantic BaseModel."
        )

    return ModelSpec(
        name=model.__name__,
        type="pydantic",
        fields=parse_fields(model, PydanticUndefined),
    )


def parse_fields(
    model: type[BaseModel], PydanticUndefined: Any
) -> tuple[FieldSpec, ...]:
    from typing import get_type_hints

    type_hints = get_type_hints(model, include_extras=True)
    field_specs = []

    for name, field_info in model.model_fields.items():
        field_type = type_hints.get(name, Any)
        field_specs.append(parse_field(field_info, field_type, name, PydanticUndefined))

    return tuple(field_specs)


def parse_field(
    field_info: FieldInfo, field_type: Any, name: str, PydanticUndefined: Any
) -> FieldSpec:
    from ...types import ENUMERATED_TYPE
    from ..constraints import (
        is_constraints_consistent,
    )
    from ..type_analysis import extract_runtime_type_and_constraints, is_nullable

    resolved_type = _resolve_pydantic_special_type(field_type)

    runtime_type, intrinsic_constraints = extract_runtime_type_and_constraints(
        resolved_type, name
    )

    all_constraints = (
        *intrinsic_constraints,
        *_parse_fieldinfo_constraints(field_info),
    )

    if not is_constraints_consistent(all_constraints):
        raise TypeError(
            f"Field '{name}': closed set (Literal/Enum) defines a fixed "
            f"set of values and cannot be combined with other constraints. "
            f"Conflicting constraints: {[type(c).__name__ for c in all_constraints]}"
        )

    nested_model = (
        parse(runtime_type)
        if runtime_type is not ENUMERATED_TYPE and supports(runtime_type)
        else None
    )

    return FieldSpec(
        name=name,
        type=runtime_type,
        constraints=all_constraints,
        default=_parse_default(field_info, PydanticUndefined),
        nullable=is_nullable(field_type),
        nested_model=nested_model,
    )


def _resolve_pydantic_special_type(field_type: Any) -> Any:
    if get_origin(field_type) is Annotated:
        field_type = get_args(field_type)[0]

    type_name = getattr(field_type, "__name__", None)
    if type_name and type_name in _PYDANTIC_TYPE_RESOLUTION:
        return _PYDANTIC_TYPE_RESOLUTION[type_name]

    return field_type


def _parse_default(field_info: FieldInfo, PydanticUndefined: Any) -> Any:
    from ...types import _UNSET

    if field_info.default_factory is not None:
        return field_info.default_factory

    if field_info.default is not PydanticUndefined:
        return field_info.default

    return _UNSET


def _parse_fieldinfo_constraints(field_info: FieldInfo) -> tuple[Constraint, ...]:
    from ...constraints import (
        ALLOWED_CONSTRAINT_TYPE,
        Constraint,
        Email,
        Pattern,
        SpecialString,
        create_constraint,
    )
    from ..constraints import _validate_constraint_type

    constraints: list[Constraint] = []

    _PYDANTIC_TYPE_MAP: dict[str, type[SpecialString]] = {"EmailStr": Email}

    annotation = field_info.annotation
    if get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]

    type_name = getattr(field_info.annotation, "__name__", None)
    if type_name and type_name in _PYDANTIC_TYPE_MAP:
        target_class = _PYDANTIC_TYPE_MAP[type_name]
        constraints.append(Pattern(regex=target_class.PATTERN))

    for meta in field_info.metadata:
        if isinstance(meta, Constraint):
            constraints.append(meta)
            continue

        for attr in ALLOWED_CONSTRAINT_TYPE:
            if hasattr(meta, attr):
                value = getattr(meta, attr)
                if value is None:
                    continue

                if attr == "pattern":
                    value = getattr(value, "pattern", value)

                constraint = create_constraint(_validate_constraint_type(attr), value)
                constraints.append(constraint)

    return tuple(constraints)
