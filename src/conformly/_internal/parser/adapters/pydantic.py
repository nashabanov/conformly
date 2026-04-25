from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin

from ..models import FieldSpec, ModelSpec

from conformly._internal.fields import SPECIAL_NAME_TO_TYPE
from conformly.exceptions import ResolutionError

if TYPE_CHECKING:
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo

    from conformly._internal.constraints import Constraint


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
        raise ResolutionError(
            f"Unsupported model type: {model}",
            context={
                "code": "unsupported_model_type",
                "model": repr(model),
                "expected": "pydantic.BaseModel",
            },
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
    from ..core import build_element_spec, build_field_spec
    from ..extractors.constraints import parse_annotated_constraints

    external_constraints = (
        *parse_annotated_constraints(field_type),
        *_parse_fieldinfo_constraints(field_info),
    )

    return build_field_spec(
        name=name,
        field_type=field_type,
        default=_parse_default(field_info, PydanticUndefined),
        external_constraints=external_constraints,
        resolve_element=lambda t, n, c: build_element_spec(
            field_name=n,
            field_type=t,
            extra_constraints=c,
            resolve_type=_resolve_pydantic_special_type,
            parse_model=parse,
            supports_model=supports,
        ),
    )


def _resolve_pydantic_special_type(field_type: Any) -> Any:
    if get_origin(field_type) is Annotated:
        field_type = get_args(field_type)[0]

    type_name = getattr(field_type, "__name__", None)
    if type_name and type_name in SPECIAL_NAME_TO_TYPE:
        return SPECIAL_NAME_TO_TYPE[type_name]

    return field_type


def _parse_default(field_info: FieldInfo, PydanticUndefined: Any) -> Any:
    from conformly._internal.types import UNSET

    if field_info.default_factory is not None:
        return field_info.default_factory

    if field_info.default is not PydanticUndefined:
        return field_info.default

    return UNSET


def _parse_fieldinfo_constraints(field_info: FieldInfo) -> tuple[Constraint, ...]:
    from ..extractors.constraints import _validate_constraint_type

    from conformly._internal.constraints import (
        ALLOWED_CONSTRAINT_TYPE,
        Constraint,
        create_constraint,
    )

    constraints: list[Constraint] = []
    origin = get_origin(field_info.annotation)
    is_collection = origin in (list, set, frozenset)

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

                target_attr = attr
                if is_collection and attr in ("min_length", "max_length"):
                    target_attr = "min_items" if attr == "min_length" else "max_items"

                constraint = create_constraint(
                    _validate_constraint_type(target_attr), value
                )
                constraints.append(constraint)

    return tuple(constraints)
