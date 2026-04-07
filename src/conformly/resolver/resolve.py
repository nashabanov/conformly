from functools import lru_cache
import math
from typing import Any
import uuid

from ..constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    MultipleOf,
    OneOf,
    Pattern,
)
from ..fields import SPECIAL_TYPE_TO_KIND, SpecialString
from ..fields.special_registry import SPECIAL_KINDS
from ..specs import FieldSpec, ModelSpec
from ..types import (
    ENUMERATED_TYPE,
    FLOAT_MAX,
    FLOAT_MIN,
    INT_MAX,
    INT_MIN,
    FieldKind,
    FieldPath,
    LengthRange,
    Range,
)
from .field import ResolvedField
from .model import ResolvedModel
from .semantics import (
    BooleanSemantic,
    EnumSemantic,
    FieldSemantics,
    ListSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
    UUIDSemantic,
)


@lru_cache(maxsize=128)
def resolve_model(spec: ModelSpec, _prefix: FieldPath = ()) -> ResolvedModel:
    model = ResolvedModel(
        name=spec.name,
        fields=tuple(
            [resolve_field(f, (*_prefix, i)) for i, f in enumerate(spec.fields)]
        ),
    )
    _build_indexes(model)
    return model


def resolve_field(field_spec: FieldSpec, path: FieldPath) -> ResolvedField:
    resolved_nested = (
        resolve_model(field_spec.nested_model, path)
        if field_spec.nested_model
        else None
    )
    list_semantic = None

    if field_spec.collection_type is list:
        list_semantic = ListSemantic(
            element_semantic=create_field_semantic(field_spec),
            element_nested_model=resolved_nested,
        )

    return ResolvedField(
        field_spec=field_spec,
        path=path,
        semantic=list_semantic or create_field_semantic(field_spec),
        nested_model=resolved_nested,
    )


def _build_indexes(model: ResolvedModel) -> None:
    if model.field_map:
        return

    field_map: dict[FieldPath, ResolvedField] = {}
    constrained_paths: list[FieldPath] = []
    all_paths: list[FieldPath] = []
    extra_paths: list[FieldPath] = []
    name_to_path: dict[str, FieldPath] = {}

    def _collect(current: ResolvedModel, prefix: FieldPath, names: list[str]) -> None:
        for i, field in enumerate(current.fields):
            path = (*prefix, i)

            field_map[path] = field
            all_paths.append(path)

            dotted = ".".join([*names, field.name])
            name_to_path[dotted] = path

            if field.semantic.has_constraints:
                constrained_paths.append(path)

            if field.nested_model:
                _collect(field.nested_model, path, [*names, field.name])

        extra_path = (*prefix, len(current.fields))
        all_paths.append(extra_path)
        extra_paths.append(extra_path)

    _collect(model, (), [])

    object.__setattr__(model, "field_map", field_map)
    object.__setattr__(model, "constrained_paths", tuple(constrained_paths))
    object.__setattr__(model, "all_paths", tuple(all_paths))
    object.__setattr__(model, "extra_paths", tuple(extra_paths))
    object.__setattr__(model, "name_to_path", name_to_path)


def create_field_semantic(field_spec: FieldSpec) -> FieldSemantics:
    t = field_spec.field_type
    c = field_spec.constraints

    if isinstance(t, type) and issubclass(t, SpecialString):
        kind = SPECIAL_TYPE_TO_KIND.get(t)
        if kind is None:
            raise NotImplementedError(
                f"No FieldKind mapped for SpecialStr subclass: {t.__name__}"
            )

        return create_string_semantic(c, kind)

    if t is uuid.UUID:
        return UUIDSemantic(has_constraints=True)

    if t is int:
        valid_bounds = calculate_numeric_bounds(t, c)
        return NumericSemantic(
            kind=FieldKind.INTEGER,
            valid_range=valid_bounds,
            invalid_ranges=calculate_invalid_numeric_ranges(
                field_type=t, bounds=valid_bounds
            ),
            has_constraints=field_spec.has_constraints(),
            multiple_of=_extract_numeric_multiple_of(c),
        )

    elif t is float:
        valid_bounds = calculate_numeric_bounds(t, c)
        return NumericSemantic(
            kind=FieldKind.FLOAT,
            valid_range=valid_bounds,
            invalid_ranges=calculate_invalid_numeric_ranges(
                field_type=t, bounds=valid_bounds
            ),
            has_constraints=field_spec.has_constraints(),
            multiple_of=_extract_numeric_multiple_of(c),
        )

    elif t is str:
        return create_string_semantic(c)

    elif field_spec.nested_model is not None:
        return ObjectSemantic(field_spec.has_constraints())

    elif t is bool:
        return BooleanSemantic(field_spec.has_constraints())

    elif t is ENUMERATED_TYPE:
        return EnumSemantic(
            extract_enum_included_values(c),
            field_spec.has_constraints(),
        )

    else:
        raise NotImplementedError(
            f"No semantics for field with type: {t} "
            f"Track progress in https://github.com/nashabanov/conformly/issues"
        )


def calculate_invalid_numeric_ranges(
    field_type: type, bounds: Range
) -> tuple[Range, ...]:
    result: list[Range] = []

    if field_type is int:
        max_offset = calculate_max_offset(int(bounds.min_value), int(bounds.max_value))

        if bounds.min_value > INT_MIN:
            result.append(
                Range(
                    min_value=bounds.min_value - max_offset,
                    max_value=bounds.min_value - 1,
                )
            )

        if bounds.max_value < INT_MAX:
            result.append(
                Range(
                    min_value=bounds.max_value + 1,
                    max_value=bounds.max_value + max_offset,
                )
            )

        return tuple(result)

    if field_type is float:
        if bounds.min_value == math.nextafter(0.0, math.inf):
            result.append(Range(min_value=-math.inf, max_value=0.0))
        elif bounds.min_value > FLOAT_MIN:
            result.append(Range(min_value=-math.inf, max_value=bounds.min_value))

        if bounds.max_value == math.nextafter(0.0, -math.inf):
            result.append(Range(min_value=0.0, max_value=math.inf))
        elif bounds.max_value < FLOAT_MAX:
            result.append(Range(min_value=bounds.max_value, max_value=math.inf))

        return tuple(result)

    raise TypeError(f"Field type must be int or float, got: {field_type}")


def calculate_max_offset(min_value: int, max_value: int) -> int:
    span = max(1, max_value - min_value)
    base = max(100, span * 2)
    return min(base, 10**6)


def calculate_numeric_bounds(
    field_type: type, constraints: tuple[Constraint, ...]
) -> Range:
    if field_type is int:
        return _calculate_int_bounds(constraints)

    if field_type is float:
        return _calculate_float_bounds(constraints)

    raise TypeError(f"Unsupported numeric type: {field_type}")


def _calculate_int_bounds(constraints: tuple[Constraint, ...]) -> Range:
    low: int = INT_MIN
    high: int = INT_MAX

    for c in constraints:
        if not isinstance(c, (GreaterThan, GreaterOrEqual, LessThan, LessOrEqual)):
            continue

        v = int(c.value)
        if isinstance(c.value, float) and math.isnan(c.value):
            raise ValueError("Constraint value cannot be NaN")

        match c:
            case GreaterThan():
                low = max(low, v + 1)
            case GreaterOrEqual():
                low = max(low, v)
            case LessThan():
                high = min(high, v - 1)
            case LessOrEqual():
                high = min(high, v)

    if low > high:
        raise ValueError(f"Invalid numeric bounds: min {low} > max {high}")
    return Range(min_value=low, max_value=high)


def _calculate_float_bounds(constraints: tuple[Constraint, ...]) -> Range:
    low: float = FLOAT_MIN
    high: float = FLOAT_MAX

    for c in constraints:
        if not isinstance(c, (GreaterThan, GreaterOrEqual, LessThan, LessOrEqual)):
            continue

        v = float(c.value)
        if math.isnan(v):
            raise ValueError("Constraint value cannot be NaN")

        match c:
            case GreaterThan():
                low = max(low, math.nextafter(v, math.inf))
            case GreaterOrEqual():
                low = max(low, v)
            case LessThan():
                high = min(high, math.nextafter(v, -math.inf))
            case LessOrEqual():
                high = min(high, v)

    if low > high:
        raise ValueError(f"Invalid numeric bounds: min {low} > max {high}")
    return Range(min_value=low, max_value=high)


def _extract_numeric_multiple_of(
    constraints: tuple[Constraint, ...],
) -> int | float | None:
    for c in constraints:
        if not isinstance(c, MultipleOf):
            continue

        return c.value

    return None


def create_string_semantic(
    constraints: tuple[Constraint, ...],
    field_kind: FieldKind = FieldKind.STRING,
) -> StringSemantic:
    has_constraints = len(constraints) > 0 or field_kind in SPECIAL_KINDS
    min_length = 0
    max_length = None
    pattern = None

    for c in constraints:
        if not isinstance(c, (MinLength, MaxLength, Pattern)):
            continue

        match c:
            case MinLength(v):
                if field_kind in (FieldKind.IPv4, FieldKind.IPv6, FieldKind.IPvAny):
                    raise ValueError(
                        f"Pattern constraint cannot be combined "
                        f"with {field_kind.value} type."
                    )
                if min_length == 0 or v > min_length:
                    min_length = v
            case MaxLength(v):
                if field_kind in (FieldKind.IPv4, FieldKind.IPv6, FieldKind.IPvAny):
                    raise ValueError(
                        f"Pattern constraint cannot be combined "
                        f"with {field_kind.value} type."
                    )
                if max_length is None or v < int(max_length):
                    max_length = v
            case Pattern(r):
                if field_kind != FieldKind.STRING:
                    raise ValueError(
                        f"Pattern constraint cannot be combined "
                        f"with {field_kind.value} type."
                    )
                if pattern is not None:
                    raise ValueError("Multiple Pattern constraints are not supported")
                pattern = r

    if max_length and min_length > max_length:
        raise ValueError(
            f"Invalid string length range: min {min_length} > max {max_length}"
        )

    return StringSemantic(
        kind=field_kind,
        length_range=LengthRange(
            min_length=min_length,
            max_length=max_length,
        ),
        pattern=pattern,
        has_constraints=has_constraints,
    )


def extract_enum_included_values(
    constraints: tuple[Constraint, ...],
) -> tuple[Any, ...]:
    if len(constraints) != 1:
        raise TypeError(
            f"Enum or Literal field must have exactly OneOf constraint, "
            f"but got {len(constraints)} constraints"
        )

    match constraints[0]:
        case OneOf(values):
            return values

        case _:
            raise TypeError(
                f"Enum or Literal field could have only OneOf constraint, "
                f"but got: {constraints[0]}"
            )
