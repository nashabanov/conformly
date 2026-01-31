import math
from typing import Any

from ..constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    OneOf,
    Pattern,
)
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
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)


def resolve_model(spec: ModelSpec, _prefix: FieldPath = ()) -> ResolvedModel:
    return ResolvedModel(
        name=spec.name,
        fields=tuple(
            [
                resolve_field(
                    f,
                    (*_prefix, i),
                )
                for i, f in enumerate(spec.fields)
            ]
        ),
    )


def resolve_field(field_spec: FieldSpec, path: FieldPath) -> ResolvedField:
    return ResolvedField(
        name=field_spec.name,
        path=path,
        py_type=field_spec.type,
        default=field_spec.default,
        nullable=field_spec.nullable,
        semantic=create_field_semantic(field_spec),
        nested_model=resolve_model(field_spec.nested_model, path)
        if field_spec.nested_model
        else None,
    )


def create_field_semantic(field_spec: FieldSpec) -> FieldSemantics:
    t = field_spec.type
    c = field_spec.constraints

    if t is int:
        valid_bounds = calculate_numeric_bounds(t, c)
        return NumericSemantic(
            kind=FieldKind.INTEGER,
            valid_range=valid_bounds,
            invalid_ranges=calculate_invalid_numeric_ranges(
                field_type=t, bounds=valid_bounds
            ),
            has_constraints=field_spec.has_constraints(),
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
        )

    elif t is str:
        return create_string_semantic(c)

    elif field_spec.nested_model is not None:
        return ObjectSemantic(FieldKind.OBJECT, field_spec.has_constraints())

    elif t is bool:
        return BooleanSemantic(FieldKind.BOOLEAN, field_spec.has_constraints())

    elif t is ENUMERATED_TYPE:
        return EnumSemantic(
            FieldKind.ENUM,
            extract_enum_included_values(c),
            field_spec.has_constraints(),
        )

    else:
        raise NotImplementedError(f"No semantics for field with type: {t} ")


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


def create_string_semantic(constraints: tuple[Constraint, ...]) -> StringSemantic:
    has_constraints = len(constraints) > 0
    min_length = 0
    max_length = None
    pattern = None

    for c in constraints:
        if not isinstance(c, (MinLength, MaxLength, Pattern)):
            continue

        match c:
            case MinLength(v):
                if min_length == 0 or v > min_length:
                    min_length = v
            case MaxLength(v):
                if max_length is None or v < int(max_length):
                    max_length = v
            case Pattern(r):
                if pattern is not None:
                    raise ValueError("Multiple Pattern constraints are not supported")
                pattern = r

    if max_length and min_length > max_length:
        raise ValueError(
            f"Invalid string length range: min {min_length} > max {max_length}"
        )

    return StringSemantic(
        kind=FieldKind.STRING,
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
