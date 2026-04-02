import math
from typing import Any

import pytest

from conformly.constraints import (
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
from conformly.fields import Email
from conformly.fields.special_registry import SPECIAL_KINDS
from conformly.resolver.resolve import (
    _build_indexes,
    _extract_numeric_multiple_of,
    calculate_invalid_numeric_ranges,
    calculate_max_offset,
    calculate_numeric_bounds,
    create_field_semantic,
    create_string_semantic,
    extract_enum_included_values,
    resolve_field,
    resolve_model,
)
from conformly.resolver.semantics import (
    BooleanSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly.resolver.semantics.enum import EnumSemantic
from conformly.specs import FieldSpec, ModelSpec
from conformly.types import (
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


@pytest.fixture
def simple_model_spec() -> ModelSpec:
    return ModelSpec(
        name="User",
        type="dataclass",
        fields=(
            FieldSpec("id", int, constraints=(GreaterThan(0),)),
            FieldSpec("name", str, constraints=(MinLength(1),)),
            FieldSpec("active", bool),
            FieldSpec(
                "type",
                ENUMERATED_TYPE,
                constraints=(OneOf(("user", "admin")),),
            ),
        ),
    )


@pytest.fixture
def nested_model_spec() -> ModelSpec:
    address = ModelSpec(
        name="Address", type="dataclass", fields=(FieldSpec("street", str),)
    )
    return ModelSpec(
        name="Person",
        type="dataclass",
        fields=(
            FieldSpec("name", str),
            FieldSpec("addr", dict, nested_model=address),
        ),
    )


# ===== TESTS for create_string_semantic() =====


@pytest.mark.parametrize(
    "constraints, expected",
    [
        (
            (MinLength(5), MaxLength(50), Pattern(r"[a-z]+")),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 50),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (MinLength(3),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(3, None),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MaxLength(100),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 100),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (Pattern(r"[a-z]+"),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (MinLength(5), Pattern(r"[a-z]+")),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (MaxLength(15), Pattern(r"[a-z]+")),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 15),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None),
                pattern=None,
                has_constraints=False,
            ),
        ),
        (
            (MinLength(0),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MaxLength(0),),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 0),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MinLength(5), MaxLength(50), Pattern(r"[a-z]+")),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 50),
                pattern=r"[a-z]+",
                has_constraints=True,
            ),
        ),
        (
            (MinLength(2), MinLength(5)),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MaxLength(20), MaxLength(10)),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 10),
                pattern=None,
                has_constraints=True,
            ),
        ),
        (
            (MinLength(3), MinLength(7), MaxLength(15), MaxLength(10)),
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(7, 10),
                pattern=None,
                has_constraints=True,
            ),
        ),
    ],
)
def test_create_string_semantic_valid(
    constraints: tuple[Constraint, ...], expected: StringSemantic
) -> None:
    semantic = create_string_semantic(constraints)
    assert semantic == expected


def test_create_email_kind_string_semantic() -> None:
    semantic = create_string_semantic((), FieldKind.EMAIL)
    assert semantic == StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(0, None),
        pattern=None,
        has_constraints=True,
    )


@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_special_string_kind_raises_with_pattern(kind: FieldKind) -> None:
    with pytest.raises(ValueError):
        create_string_semantic(constraints=(Pattern(r"\d+"),), field_kind=kind)


@pytest.mark.parametrize("kind", [FieldKind.IPv4, FieldKind.IPv6, FieldKind.IPvAny])
def test_ip_string_kind_raises_with_lengths(kind: FieldKind) -> None:
    with pytest.raises(ValueError):
        create_string_semantic(constraints=(MinLength(1),), field_kind=kind)

    with pytest.raises(ValueError):
        create_string_semantic(constraints=(MaxLength(25),), field_kind=kind)


def test_create_string_semantic_ignore_other_constraints() -> None:
    assert create_string_semantic(constraints=(GreaterOrEqual(1),)) == StringSemantic(
        kind=FieldKind.STRING,
        length_range=LengthRange(0, None),
        pattern=None,
        has_constraints=True,
    )


def test_create_string_semantic_invalid_bounds() -> None:
    with pytest.raises(ValueError):
        create_string_semantic((MinLength(10), MaxLength(3)))


def test_create_string_semantic_double_patten() -> None:
    with pytest.raises(ValueError):
        create_string_semantic((Pattern(r"\d+"), Pattern(r"[0-9]{3}")))


# ===== TESTS for calculate_numeric_bounds() =====


@pytest.mark.parametrize(
    "field_type, constraints, expected_range",
    [
        (int, (), Range(INT_MIN, INT_MAX)),
        (int, (GreaterOrEqual(5),), Range(5, INT_MAX)),
        (int, (GreaterThan(10),), Range(11, INT_MAX)),
        (int, (LessOrEqual(100),), Range(INT_MIN, 100)),
        (int, (LessThan(20),), Range(INT_MIN, 19)),
        (int, (GreaterOrEqual(10), LessThan(50)), Range(10, 49)),
        (
            int,
            (GreaterThan(5), GreaterOrEqual(10), LessThan(100), LessOrEqual(90)),
            Range(10, 90),
        ),
        (float, (), Range(FLOAT_MIN, FLOAT_MAX)),
        (float, (GreaterOrEqual(2.0),), Range(2.0, FLOAT_MAX)),
        (
            float,
            (GreaterThan(1.5),),
            Range(math.nextafter(1.5, math.inf), FLOAT_MAX),
        ),
        (float, (LessOrEqual(4.2),), Range(FLOAT_MIN, 4.2)),
        (
            float,
            (LessThan(3.7),),
            Range(FLOAT_MIN, math.nextafter(3.7, -math.inf)),
        ),
        (
            float,
            (GreaterOrEqual(1.0), LessThan(2.0)),
            Range(1.0, math.nextafter(2.0, -math.inf)),
        ),
    ],
)
def test_calculate_numeric_bounds_valid(field_type, constraints, expected_range):
    result = calculate_numeric_bounds(field_type, constraints)
    assert result == expected_range


@pytest.mark.parametrize(
    "field_type, constraints",
    [
        (int, (GreaterThan(10), LessThan(5))),
        (int, (GreaterOrEqual(10), LessThan(9))),
        (float, (GreaterThan(5.0), LessThan(3.0))),
        (float, (GreaterOrEqual(2.0), LessThan(1.9))),
    ],
)
def test_calculate_numeric_bounds_invalid_raises(
    field_type: type, constraints: tuple[Constraint, ...]
):
    with pytest.raises(ValueError):
        calculate_numeric_bounds(field_type, constraints)


@pytest.mark.parametrize("field_type", [int, float])
def test_calculate_numeric_bounds_raises_on_nan(field_type: type) -> None:
    with pytest.raises(ValueError):
        calculate_numeric_bounds(field_type, (GreaterOrEqual(math.nan),))


# ===== TESTS for calculate_invalid_numeric_ranges =====


@pytest.mark.parametrize(
    "field_type, bounds, expected_ranges",
    [
        (
            int,
            Range(10, 20),
            (
                Range(10 - calculate_max_offset(10, 20), 9),
                Range(21, 20 + calculate_max_offset(10, 20)),
            ),
        ),
        (
            int,
            Range(INT_MIN, 100),
            (Range(101, 100 + calculate_max_offset(INT_MIN, 100)),),
        ),
        (
            int,
            Range(50, INT_MAX),
            (Range(50 - calculate_max_offset(50, INT_MAX), 49),),
        ),
        (
            int,
            Range(INT_MIN, INT_MAX),
            (),
        ),
        (
            int,
            Range(0, 0),
            (
                Range(0 - calculate_max_offset(0, 0), -1),
                Range(1, 0 + calculate_max_offset(0, 0)),
            ),
        ),
        (
            float,
            Range(1.5, 3.7),
            (
                Range(-math.inf, 1.5),
                Range(3.7, math.inf),
            ),
        ),
        (
            float,
            Range(-math.inf, 100.0),
            (Range(100.0, math.inf),),
        ),
        (
            float,
            Range(-5.0, math.inf),
            (Range(-math.inf, -5.0),),
        ),
        (
            float,
            Range(-math.inf, math.inf),
            (),
        ),
        (
            float,
            Range(0.0, 0.0),
            (
                Range(-math.inf, 0.0),
                Range(0.0, math.inf),
            ),
        ),
    ],
)
def test_calculate_invalid_numeric_ranges(field_type, bounds, expected_ranges):
    result = calculate_invalid_numeric_ranges(field_type, bounds)

    assert len(result) == len(expected_ranges)
    for r, exp in zip(result, expected_ranges):
        assert r.min_value == exp.min_value
        assert r.max_value == exp.max_value


def test_unsupported_field_type():
    with pytest.raises(TypeError, match="Field type must be int or float"):
        calculate_invalid_numeric_ranges(str, Range(0, 1))


# ===== TESTS for create_string_semantic() =====


@pytest.mark.parametrize(
    "field_type, constraints, nested_model, expected_semantic_type",
    [
        (int, (), None, NumericSemantic),
        (float, (), None, NumericSemantic),
        (str, (), None, StringSemantic),
        (bool, (), None, BooleanSemantic),
        (dict, (), ModelSpec("Inner", "dataclass", ()), ObjectSemantic),
        (Email, (), None, StringSemantic),
    ],
)
def test_create_field_semantic_dispatch(
    field_type: type,
    constraints: tuple[Constraint, ...],
    nested_model: ModelSpec | None,
    expected_semantic_type,
) -> None:
    field_spec = FieldSpec(
        name="test",
        field_type=field_type,
        constraints=constraints,
        nested_model=nested_model,
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


# ===== TESTS for extract_enum_included_values() =====


@pytest.mark.parametrize(
    "constraints, extracted",
    [
        ((OneOf((1, 2, 3)),), (1, 2, 3)),
        ((OneOf(("a", "b", "c")),), ("a", "b", "c")),
        ((OneOf(()),), ()),
    ],
)
def test_extract_enum_included_values_valid(
    constraints: tuple[Constraint], extracted: tuple[Any, ...]
) -> None:
    assert extract_enum_included_values(constraints) == extracted


def test_extract_enum_included_values_more_than_one_constraints() -> None:
    with pytest.raises(TypeError):
        extract_enum_included_values((OneOf((1, 2)), MaxLength(1)))


def test_extract_enum_included_values_not_one_of() -> None:
    with pytest.raises(TypeError):
        extract_enum_included_values((MaxLength(1),))


# ===== TESTS for _extract_numeric_multiple_of


@pytest.mark.parametrize(
    "constraints, expected",
    [
        ((MultipleOf(2),), 2),
        ((MultipleOf(2.0), LessOrEqual(10)), 2.0),
        ((LessOrEqual(2.0),), None),
    ],
)
def test_extract_numeric_multiple_of(
    constraints: tuple[Constraint, ...], expected: int | float | None
) -> None:
    assert _extract_numeric_multiple_of(constraints) == expected


# ===== TESTS for resolve_field() =====


def test_resolve_field_flat() -> None:
    field_spec = FieldSpec(
        name="count",
        field_type=int,
        default=43,
        nullable=False,
        constraints=(GreaterThan(2),),
    )
    path: FieldPath = (1, 3)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "count"
    assert resolved.path == (1, 3)
    assert resolved.py_type is int
    assert resolved.default == 43
    assert resolved.nullable is False
    assert isinstance(resolved.semantic, NumericSemantic)
    assert resolved.nested_model is None
    assert resolved.semantic.has_constraints is True


def test_resolve_field_with_nested_model():
    inner = ModelSpec("Point", "dataclass", (FieldSpec("x", int), FieldSpec("y", int)))
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
    assert len(resolved.fields) == 4

    id_field = resolved.fields[0]
    assert id_field.name == "id"
    assert id_field.path == (0,)
    assert isinstance(id_field.semantic, NumericSemantic)

    name_field = resolved.fields[1]
    assert name_field.name == "name"
    assert name_field.path == (1,)
    assert isinstance(name_field.semantic, StringSemantic)

    active_field = resolved.fields[2]
    assert active_field.name == "active"
    assert active_field.path == (2,)
    assert isinstance(active_field.semantic, BooleanSemantic)

    type_field = resolved.fields[3]
    assert type_field.name == "type"
    assert type_field.path == (3,)
    assert isinstance(type_field.semantic, EnumSemantic)

    assert len(resolved.field_map) == 4
    assert len(resolved.constrained_paths) == 3
    assert len(resolved.all_paths) == 5


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

    assert len(resolved.field_map) == 3
    assert len(resolved.constrained_paths) == 0
    assert len(resolved.all_paths) == 5


def test_resolve_model_empty():
    spec = ModelSpec("Empty", "dataclass", ())
    resolved = resolve_model(spec)
    assert resolved.name == "Empty"
    assert resolved.fields == ()
    assert resolved.field_map == {}
    assert resolved.constrained_paths == ()
    assert resolved.all_paths == ((0,),)


# ===== TESTS for _build_indexes() =====


def test_build_indexes_flat(simple_model_spec) -> None:
    resolved = resolve_model(simple_model_spec)
    _build_indexes(resolved)

    assert len(resolved.field_map) == 4
    assert (0,) in resolved.field_map
    assert (1,) in resolved.field_map
    assert (2,) in resolved.field_map
    assert (3,) in resolved.field_map

    assert resolved.field_map[(0,)].field_spec.name == "id"
    assert resolved.field_map[(1,)].field_spec.name == "name"
    assert resolved.field_map[(2,)].field_spec.name == "active"
    assert resolved.field_map[(3,)].field_spec.name == "type"

    assert (0,) in resolved.constrained_paths
    assert (1,) in resolved.constrained_paths
    assert (2,) not in resolved.constrained_paths
    assert (3,) in resolved.constrained_paths
    assert len(resolved.constrained_paths) == 3

    assert len(resolved.all_paths) == 5
    assert (0,) in resolved.all_paths
    assert (1,) in resolved.all_paths
    assert (2,) in resolved.all_paths
    assert (3,) in resolved.all_paths
    assert (4,) in resolved.all_paths

    assert len(resolved.extra_paths) == 1
    assert (4,) in resolved.extra_paths

    assert "id" in resolved.name_to_path
    assert "name" in resolved.name_to_path
    assert resolved.name_to_path["id"] == (0,)
    assert resolved.name_to_path["name"] == (1,)


def test_nested_field_map_contains_all_levels(nested_model_spec):
    model = resolve_model(nested_model_spec)
    _build_indexes(model)

    assert (0,) in model.field_map
    assert (1,) in model.field_map
    assert (1, 0) in model.field_map
    assert len(model.field_map) == 3


def test_nested_all_paths_has_extra_at_each_level(nested_model_spec):
    model = resolve_model(nested_model_spec)
    _build_indexes(model)

    assert (0,) in model.all_paths
    assert (1,) in model.all_paths
    assert (2,) in model.all_paths
    assert (1, 0) in model.all_paths
    assert (1, 1) in model.all_paths
    assert len(model.all_paths) == 5

    assert len(model.extra_paths) == 2
    assert (2,) in model.extra_paths
    assert (1, 1) in model.extra_paths

    assert len(model.name_to_path) == 3
    assert "addr.street" in model.name_to_path


def test_nested_constrained_paths_empty_if_no_constraints(nested_model_spec):
    model = resolve_model(nested_model_spec)
    _build_indexes(model)
    assert len(model.constrained_paths) == 0


def test_ensure_indexes_is_idempotent(simple_model_spec):
    model = resolve_model(simple_model_spec)

    _build_indexes(model)

    first_all_paths_len = len(model.all_paths)
    first_field_map_len = len(model.field_map)

    _build_indexes(model)

    assert len(model.all_paths) == first_all_paths_len
    assert len(model.field_map) == first_field_map_len


def test_extra_path_index_equals_fields_count(simple_model_spec):
    model = resolve_model(simple_model_spec)
    _build_indexes(model)

    extra_paths = [p for p in model.all_paths if p not in model.field_map]

    assert len(extra_paths) == 1
    assert extra_paths[0] == (len(model.fields),)
