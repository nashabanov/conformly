import math
import sys

from ..constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    Pattern,
)
from ..specs import FieldSpec, ModelSpec
from ..types import FieldKind, FieldPath, LengthRange, Range
from .field import ResolvedField
from .model import ResolvedModel
from .semantics import (
    BooleanSemantic,
    FieldSemantics,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)


def resolve_model(spec: ModelSpec, _prefix: FieldPath = ()) -> ResolvedModel:
    return ResolvedModel(
        name=spec.name,
        fields=[
            resolve_field(
                f,
                (
                    *_prefix,
                    i,
                ),
            )
            for i, f in enumerate(spec.fields)
        ],
    )


def resolve_field(field_spec: FieldSpec, path: FieldPath) -> ResolvedField:
    return ResolvedField(
        name=field_spec.name,
        path=path,
        py_type=field_spec.type,
        default=field_spec.default,
        nullable=field_spec.nullable,
        semantics=create_field_semantic(field_spec),
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
        )

    elif t is float:
        valid_bounds = calculate_numeric_bounds(t, c)
        return NumericSemantic(
            kind=FieldKind.FLOAT,
            valid_range=valid_bounds,
            invalid_ranges=calculate_invalid_numeric_ranges(
                field_type=t, bounds=valid_bounds
            ),
        )

    elif t is str:
        return create_string_semantic(c)

    elif field_spec.nested_model is not None:
        return ObjectSemantic(FieldKind.OBJECT)

    elif t is bool:
        return BooleanSemantic(FieldKind.BOOLEAN)

    else:
        raise NotImplementedError(f"No semantics for field with type: {t} ")


def calculate_invalid_numeric_ranges(
    field_type: type, bounds: Range
) -> tuple[Range, ...]:
    if field_type is int:
        max_offset = calculate_max_offset(int(bounds.min_value), int(bounds.max_value))
        result = []

        if bounds.has_min:
            result.append(
                Range(
                    min_value=bounds.min_value - max_offset,
                    max_value=bounds.min_value - 1,
                    has_min=True,
                    has_max=True,
                )
            )

        if bounds.has_max:
            result.append(
                Range(
                    min_value=bounds.max_value + 1,
                    max_value=bounds.max_value + max_offset,
                    has_min=True,
                    has_max=True,
                )
            )

        return tuple(result)

    if field_type is float:
        result = []

        if bounds.has_min:
            result.append(
                Range(
                    min_value=-math.inf,
                    max_value=bounds.min_value,
                    has_min=True,
                    has_max=True,
                )
            )

        if bounds.has_max:
            result.append(
                Range(
                    min_value=bounds.max_value,
                    max_value=math.inf,
                    has_min=True,
                    has_max=True,
                )
            )

        return tuple(result)

    raise TypeError(f"Field type must be int or float, got: {field_type}")


def calculate_max_offset(min_value: int, max_value: int) -> int:
    span = max(1, max_value - min_value)
    base = max(100, span * 2)
    return min(base, 10**6)


def calculate_numeric_bounds(field_type: type, constraints: list[Constraint]) -> Range:
    low = -(2**63) if field_type is int else -sys.float_info.max
    high = 2**63 - 1 if field_type is int else sys.float_info.max
    has_min = False
    has_max = False

    for c in constraints:
        if not isinstance(c, (GreaterThan, GreaterOrEqual, LessThan, LessOrEqual)):
            continue

        v = int(c.value) if field_type is int else float(c.value)

        if math.isnan(v):
            raise ValueError("Constraint value cannot be NaN")

        match c:
            case GreaterThan():
                low = max(
                    low, v + 1 if field_type is int else math.nextafter(v, math.inf)
                )
                has_min = True
            case GreaterOrEqual():
                low = max(low, v)
                has_min = True
            case LessThan():
                high = min(
                    high, v - 1 if field_type is int else math.nextafter(v, -math.inf)
                )
                has_max = True
            case LessOrEqual():
                high = min(high, v)
                has_max = True
    if low > high:
        raise ValueError(
            f"Min value cannot be higher than max value: min: {low}, max {high}"
        )
    return Range(min_value=low, max_value=high, has_min=has_min, has_max=has_max)


def create_string_semantic(constraints: list[Constraint]) -> StringSemantic:
    min_length = 0
    max_length = None
    has_min = False
    has_max = False
    pattern = None

    for c in constraints:
        if not isinstance(c, (MinLength, MaxLength, Pattern)):
            continue

        match c:
            case MinLength(v):
                if not has_min or v > min_length:
                    min_length = v
                has_min = True
            case MaxLength(v):
                if max_length is None or v < int(max_length):
                    max_length = v
                has_max = True
            case Pattern(r):
                if pattern is not None:
                    raise ValueError("Multiple Pattern constraints are not supported")
                pattern = r

    if max_length and min_length > max_length:
        raise ValueError(
            "Min length cannot be higher than max length: "
            f"min: {min_length}, max: {max_length}"
        )

    return StringSemantic(
        kind=FieldKind.STRING,
        length_range=LengthRange(
            min_length=min_length,
            max_length=max_length,
            has_min=has_min,
            has_max=has_max,
        ),
        pattern=pattern,
    )
