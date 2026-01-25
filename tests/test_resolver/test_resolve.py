import math
import sys

import pytest

from conformly.constraints import (
    Constraint,
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    Pattern,
)
from conformly.resolver.resolve import (
    calculate_invalid_numeric_ranges,
    calculate_max_offset,
    calculate_numeric_bounds,
    create_field_semantic,
    create_string_semantic,
    resolve_field,
    resolve_model,
)
from conformly.resolver.semantics import (
    BooleanSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly.specs import FieldSpec, ModelSpec
from conformly.types import FieldKind, FieldPath, LengthRange, Range

INT_MIN = -(2**63)
INT_MAX = 2**63 - 1
FLOAT_MIN = -sys.float_info.max
FLOAT_MAX = sys.float_info.max


@pytest.fixture
def simple_model_spec() -> ModelSpec:
    return ModelSpec(
        name="User",
        type="dataclass",
        fields=[
            FieldSpec("id", int, constraints=[GreaterThan(0)]),
            FieldSpec("name", str, constraints=[MinLength(1)]),
            FieldSpec("active", bool),
        ],
    )


@pytest.fixture
def nested_model_spec() -> ModelSpec:
    address = ModelSpec(
        name="Address", type="dataclass", fields=[FieldSpec("street", str)]
    )
    return ModelSpec(
        name="Person",
        type="dataclass",
        fields=[
            FieldSpec("name", str),
            FieldSpec("addr", dict, nested_model=address),
        ],
    )


# ===== TESTS for create_string_semantic() =====


@pytest.mark.parametrize(
    "constraints, expected",
    [
        (
            [MinLength(5), MaxLength(50), Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 50, True, True),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [MinLength(3)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(3, None, True, False),
                pattern=None,
            ),
        ),
        (
            [MaxLength(100)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 100, False, True),
                pattern=None,
            ),
        ),
        (
            [Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None, False, False),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [MinLength(5), Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None, True, False),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [MaxLength(15), Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 15, False, True),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None, False, False),
                pattern=None,
            ),
        ),
        (
            [MinLength(0)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None, True, False),
                pattern=None,
            ),
        ),
        (
            [MaxLength(0)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 0, False, True),
                pattern=None,
            ),
        ),
        (
            [MinLength(5), MaxLength(50), Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 50, True, True),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [MinLength(2), MinLength(5)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None, has_min=True, has_max=False),
                pattern=None,
            ),
        ),
        (
            [MaxLength(20), MaxLength(10)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 10, has_min=False, has_max=True),
                pattern=None,
            ),
        ),
        (
            [MinLength(3), MinLength(7), MaxLength(15), MaxLength(10)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(7, 10, has_min=True, has_max=True),
                pattern=None,
            ),
        ),
    ],
)
def test_create_string_semantic_valid(
    constraints: list[Constraint], expected: StringSemantic
) -> None:
    semantic = create_string_semantic(constraints)
    assert semantic == expected


def test_create_string_semantic_invalid_bounds() -> None:
    with pytest.raises(ValueError):
        create_string_semantic([MinLength(10), MaxLength(3)])


def test_create_string_semantic_double_patten() -> None:
    with pytest.raises(ValueError):
        create_string_semantic([Pattern(r"\d+"), Pattern(r"[0-9]{3}")])


# ===== TESTS for calculate_numeric_bounds() =====


@pytest.mark.parametrize(
    "field_type, constraints, expected_range",
    [
        (int, [], Range(INT_MIN, INT_MAX, False, False)),
        (int, [GreaterOrEqual(5)], Range(5, INT_MAX, True, False)),
        (int, [GreaterThan(10)], Range(11, INT_MAX, True, False)),
        (int, [LessOrEqual(100)], Range(INT_MIN, 100, False, True)),
        (int, [LessThan(20)], Range(INT_MIN, 19, False, True)),
        (int, [GreaterOrEqual(10), LessThan(50)], Range(10, 49, True, True)),
        (
            int,
            [GreaterThan(5), GreaterOrEqual(10), LessThan(100), LessOrEqual(90)],
            Range(10, 90, True, True),
        ),
        (float, [], Range(FLOAT_MIN, FLOAT_MAX, False, False)),
        (float, [GreaterOrEqual(2.0)], Range(2.0, FLOAT_MAX, True, False)),
        (
            float,
            [GreaterThan(1.5)],
            Range(math.nextafter(1.5, math.inf), FLOAT_MAX, True, False),
        ),
        (float, [LessOrEqual(4.2)], Range(FLOAT_MIN, 4.2, False, True)),
        (
            float,
            [LessThan(3.7)],
            Range(FLOAT_MIN, math.nextafter(3.7, -math.inf), False, True),
        ),
        (
            float,
            [GreaterOrEqual(1.0), LessThan(2.0)],
            Range(1.0, math.nextafter(2.0, -math.inf), True, True),
        ),
    ],
)
def test_calculate_numeric_bounds_valid(field_type, constraints, expected_range):
    result = calculate_numeric_bounds(field_type, constraints)
    assert result == expected_range


@pytest.mark.parametrize(
    "field_type, constraints",
    [
        (int, [GreaterThan(10), LessThan(5)]),
        (int, [GreaterOrEqual(10), LessThan(9)]),
        (float, [GreaterThan(5.0), LessThan(3.0)]),
        (float, [GreaterOrEqual(2.0), LessThan(1.9)]),
    ],
)
def test_calculate_numeric_bounds_invalid_raises(field_type, constraints):
    with pytest.raises(ValueError):
        calculate_numeric_bounds(field_type, constraints)


# ===== TESTS for calculate_invalid_numeric_ranges =====


@pytest.mark.parametrize(
    "field_type, bounds, expected_ranges",
    [
        (
            int,
            Range(10, 20, has_min=True, has_max=True),
            (
                Range(10 - calculate_max_offset(10, 20), 9, True, True),
                Range(21, 20 + calculate_max_offset(10, 20), True, True),
            ),
        ),
        (
            int,
            Range(INT_MIN, 100, has_min=True, has_max=False),
            (
                Range(
                    INT_MIN - calculate_max_offset(INT_MIN, 100),
                    INT_MIN - 1,
                    True,
                    True,
                ),
            ),
        ),
        (
            int,
            Range(50, INT_MAX, has_min=False, has_max=True),
            (
                Range(
                    INT_MAX + 1, INT_MAX + calculate_max_offset(50, INT_MAX), True, True
                ),
            ),
        ),
        (
            int,
            Range(0, 0, has_min=True, has_max=True),
            (
                Range(0 - calculate_max_offset(0, 0), -1, True, True),
                Range(1, 0 + calculate_max_offset(0, 0), True, True),
            ),
        ),
        (
            int,
            Range(0, 0, has_min=False, has_max=False),
            (),
        ),
        (
            float,
            Range(1.5, 3.7, has_min=True, has_max=True),
            (
                Range(-math.inf, 1.5, True, True),
                Range(3.7, math.inf, True, True),
            ),
        ),
        (
            float,
            Range(-10.0, 100.0, has_min=True, has_max=False),
            (Range(-math.inf, -10.0, True, True),),
        ),
        (
            float,
            Range(-5.0, 5.0, has_min=False, has_max=True),
            (Range(5.0, math.inf, True, True),),
        ),
        (
            float,
            Range(0.0, 0.0, has_min=False, has_max=False),
            (),
        ),
    ],
)
def test_calculate_invalid_numeric_ranges(field_type, bounds, expected_ranges):
    result = calculate_invalid_numeric_ranges(field_type, bounds)

    assert len(result) == len(expected_ranges)
    for r, exp in zip(result, expected_ranges):
        assert r.min_value == exp.min_value
        assert r.max_value == exp.max_value
        assert r.has_min == exp.has_min
        assert r.has_max == exp.has_max


def test_unsupported_field_type():
    with pytest.raises(TypeError, match="Field type must be int or float"):
        calculate_invalid_numeric_ranges(str, Range(0, 1, True, True))


# ===== TESTS for create_string_semantic() =====


@pytest.mark.parametrize(
    "field_type, constraints, nested_model, expected_semantic_type",
    [
        (int, [], None, NumericSemantic),
        (float, [], None, NumericSemantic),
        (str, [], None, StringSemantic),
        (bool, [], None, BooleanSemantic),
        (dict, [], ModelSpec("Inner", "dataclass", []), ObjectSemantic),
    ],
)
def test_create_field_semantic_dispatch(
    field_type: type,
    constraints: list[Constraint],
    nested_model: ModelSpec | None,
    expected_semantic_type,
) -> None:
    field_spec = FieldSpec(
        name="test", type=field_type, constraints=constraints, nested_model=nested_model
    )

    semantic = create_field_semantic(field_spec)
    assert isinstance(semantic, expected_semantic_type)

    if expected_semantic_type is NumericSemantic:
        assert semantic.kind == (
            FieldKind.INTEGER if field_type is int else FieldKind.FLOAT
        )


def test_create_field_semantic_unsupported_type() -> None:
    field_spec = FieldSpec("x", bytes)
    with pytest.raises(NotImplementedError):
        create_field_semantic(field_spec)


# ===== TESTS for resolve_field() =====


def test_resolve_field_flat() -> None:
    field_spec = FieldSpec(
        name="count", type=int, default=43, nullable=False, constraints=[GreaterThan(2)]
    )
    path: FieldPath = (1, 3)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "count"
    assert resolved.path == (1, 3)
    assert resolved.py_type is int
    assert resolved.default == 43
    assert resolved.nullable is False
    assert isinstance(resolved.semantics, NumericSemantic)
    assert resolved.nested_model is None


def test_resolve_field_with_nested_model():
    inner = ModelSpec("Point", "dataclass", [FieldSpec("x", int), FieldSpec("y", int)])
    field_spec = FieldSpec("origin", dict, nested_model=inner)
    path: FieldPath = (0,)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "origin"
    assert resolved.path == (0,)
    assert resolved.nested_model is not None
    assert resolved.nested_model.name == "Point"
    assert len(resolved.nested_model.fields) == 2
    assert resolved.nested_model.fields[0].name == "x"
    assert resolved.nested_model.fields[0].path == (0, 0)
    assert resolved.nested_model.fields[1].path == (0, 1)


# ===== TESTS for resolve_model() =====


def test_resolve_model_flat(simple_model_spec):
    resolved = resolve_model(simple_model_spec)

    assert resolved.name == "User"
    assert len(resolved.fields) == 3

    id_field = resolved.fields[0]
    assert id_field.name == "id"
    assert id_field.path == (0,)
    assert isinstance(id_field.semantics, NumericSemantic)

    name_field = resolved.fields[1]
    assert name_field.name == "name"
    assert name_field.path == (1,)
    assert isinstance(name_field.semantics, StringSemantic)

    active_field = resolved.fields[2]
    assert active_field.name == "active"
    assert active_field.path == (2,)
    assert isinstance(active_field.semantics, BooleanSemantic)


def test_resolve_model_nested(nested_model_spec):
    resolved = resolve_model(nested_model_spec)

    assert resolved.name == "Person"
    assert len(resolved.fields) == 2

    addr_field = resolved.fields[1]
    assert addr_field.name == "addr"
    assert addr_field.path == (1,)
    assert addr_field.nested_model is not None
    assert addr_field.nested_model.name == "Address"

    street = addr_field.nested_model.fields[0]
    assert street.name == "street"
    assert street.path == (1, 0)


def test_resolve_model_empty():
    spec = ModelSpec("Empty", "dataclass", [])
    resolved = resolve_model(spec)
    assert resolved.name == "Empty"
    assert resolved.fields == []
