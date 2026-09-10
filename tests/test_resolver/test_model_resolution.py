import pytest

from conformly._internal.constraints import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    MaxItems,
    MaxLength,
    MinItems,
    MinLength,
    UniqueItems,
)
from conformly._internal.fields import Email
from conformly._internal.parser import ElementSpec, FieldSpec, ModelSpec
from conformly._internal.resolver import ResolvedModel
from conformly._internal.resolver.resolve import (
    _build_indexes,
    resolve_field,
    resolve_model,
)
from conformly._internal.resolver.semantics import (
    BooleanSemantic,
    EnumSemantic,
    ListSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly._internal.resolver.semantics.dict import DictSemantic
from conformly._internal.types import (
    FieldKind,
    FieldPath,
)
from conformly.exceptions import ResolutionError, SchemaError

# ===== TESTS for resolve_field() =====


def test_resolve_field_flat() -> None:
    field_spec = FieldSpec(
        name="count",
        element=ElementSpec(int, (GreaterThan(2),)),
        default=43,
        nullable=False,
    )
    path: FieldPath = (1, 3)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "count"
    assert resolved.path == path
    assert resolved.py_type is int
    assert resolved.default == 43
    assert resolved.nullable is False
    assert isinstance(resolved.semantic, NumericSemantic)
    assert resolved.nested_model is None
    assert resolved.semantic.has_constraints is True


def test_resolve_field_with_nested_model():
    inner = ModelSpec(
        "Point",
        "dataclass",
        (
            FieldSpec(name="x", element=ElementSpec(int, ())),
            FieldSpec(name="y", element=ElementSpec(int, ())),
        ),
    )
    field_spec = FieldSpec(
        name="origin", element=ElementSpec(dict, (), nested_model=inner)
    )
    path: FieldPath = (0,)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "origin"
    assert resolved.path == path
    assert resolved.nested_model is not None
    assert resolved.nested_model.name == "Point"
    assert len(resolved.nested_model.fields) == 2
    assert resolved.nested_model.fields[0].name == "x"
    assert resolved.nested_model.fields[0].path == (0, 0)
    assert resolved.nested_model.fields[1].path == (0, 1)


def test_resolve_list_field() -> None:
    field_spec = FieldSpec(
        name="emails", item=ElementSpec(Email, ()), collection_type=list
    )
    path: FieldPath = (0,)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "emails"
    assert resolved.path == path
    assert isinstance(resolved.semantic, ListSemantic)
    assert isinstance(resolved.semantic.element_semantic, StringSemantic)


def test_resolve_list_with_constrained_type() -> None:
    field_spec = FieldSpec(
        name="nums",
        item=ElementSpec(int, (GreaterOrEqual(10), LessOrEqual(100))),
        collection_type=list,
    )
    path: FieldPath = (1, 2)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "nums"
    assert resolved.path == path
    assert isinstance(resolved.semantic, ListSemantic)
    assert isinstance(resolved.semantic.element_semantic, NumericSemantic)
    assert resolved.semantic.element_semantic.kind == FieldKind.INTEGER
    assert resolved.semantic.element_semantic.has_constraints is True
    assert len(resolved.semantic.element_semantic.invalid_ranges) == 2


def test_resolve_list_with_nested_model(simple_model_spec) -> None:
    field_spec = FieldSpec(
        name="models",
        item=ElementSpec(type, (), simple_model_spec),
        collection_type=list,
    )
    path: FieldPath = (1, 2)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "models"
    assert resolved.path == path
    assert isinstance(resolved.semantic, ListSemantic)
    assert isinstance(resolved.semantic.element_nested_model, ResolvedModel)
    assert isinstance(resolved.semantic.element_semantic, ObjectSemantic)


def test_resolve_constrained_list_type() -> None:
    field_spec = FieldSpec(
        name="names",
        item=ElementSpec(str, (MinLength(1), MaxLength(10))),
        collection_type=list,
        collection_constraints=(MinItems(10), MaxItems(15), UniqueItems(True)),
    )
    path: FieldPath = (1, 2)

    resolved = resolve_field(field_spec, path)
    semantic = resolved.semantic

    assert isinstance(semantic, ListSemantic)
    assert isinstance(semantic.element_semantic, StringSemantic)
    assert semantic.has_constraints is True
    assert semantic.is_unique_items is True
    assert semantic.length_range is not None
    assert semantic.length_range.min_length == 10
    assert semantic.length_range.max_length == 15
    assert semantic.element_semantic.length_range.min_length == 1
    assert semantic.element_semantic.length_range.max_length == 10
    assert semantic.element_semantic.has_constraints is True


def test_resolve_list_invalid_range_raises() -> None:
    field_spec = FieldSpec(
        name="names",
        item=ElementSpec(str, ()),
        collection_type=list,
        collection_constraints=(MinItems(20), MaxItems(15), UniqueItems(True)),
    )

    with pytest.raises(SchemaError):
        resolve_field(field_spec, (1,))


def test_resolve_dict_field() -> None:
    field_spec = FieldSpec(
        name="emails",
        key=ElementSpec(str, (MaxLength(15),)),
        value=ElementSpec(Email, ()),
        collection_type=dict,
    )
    path: FieldPath = (0,)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "emails"
    assert resolved.path == path
    assert isinstance(resolved.semantic, DictSemantic)
    assert isinstance(resolved.semantic.key_semantic, StringSemantic)
    assert resolved.semantic.key_semantic.has_constraints is True
    assert resolved.semantic.key_semantic.length_range.max_length == 15
    assert isinstance(resolved.semantic.value_semantic, StringSemantic)
    assert resolved.semantic.value_semantic.kind == FieldKind.EMAIL


def test_resolve_constrained_dict_type(simple_model_spec) -> None:
    field_spec = FieldSpec(
        name="models",
        key=ElementSpec(str, (MaxLength(15),)),
        value=ElementSpec(simple_model_spec, (), nested_model=simple_model_spec),
        collection_type=dict,
        collection_constraints=(UniqueItems(True), MaxItems(5)),
    )
    path: FieldPath = (0,)

    resolved = resolve_field(field_spec, path)

    assert resolved.name == "models"
    assert resolved.path == path
    assert isinstance(resolved.semantic, DictSemantic)
    assert resolved.semantic.has_constraints is True
    assert resolved.semantic.length_range is not None
    assert resolved.semantic.length_range.max_length == 5
    assert resolved.semantic.is_unique_items is False
    assert isinstance(resolved.semantic.key_semantic, StringSemantic)
    assert resolved.semantic.key_semantic.has_constraints is True
    assert resolved.semantic.key_semantic.length_range.max_length == 15
    assert isinstance(resolved.semantic.value_semantic, ObjectSemantic)
    assert isinstance(resolved.semantic.value_nested_model, ResolvedModel)


@pytest.mark.parametrize("key_type", [int, list, ResolvedModel, bool])
def test_resolve_dict_field_invalid_key_type_raises(key_type: type) -> None:
    field_spec = FieldSpec(
        name="emails",
        key=ElementSpec(key_type, (MaxLength(15),)),
        value=ElementSpec(Email, ()),
        collection_type=dict,
    )
    path: FieldPath = (0,)

    with pytest.raises(ResolutionError):
        resolve_field(field_spec, path)


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
