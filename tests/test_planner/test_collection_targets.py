import pytest
from semantic_factories import numeric_semantic, string_semantic

from conformly._internal.parser import ElementSpec, FieldSpec
from conformly._internal.planner import plan_violation_task
from conformly._internal.planner.field import _define_allowed_violation_types
from conformly._internal.planner.model import CollectionTarget
from conformly._internal.resolver import ResolvedField
from conformly._internal.resolver.resolve import create_resolved_model
from conformly._internal.resolver.semantics import (
    BooleanSemantic,
    DictSemantic,
    EnumSemantic,
    ListSemantic,
    TupleSemantic,
)
from conformly._internal.types import LengthRange, ViolationType as V
from conformly.exceptions import PlanningError


def model_for(semantic):
    return create_resolved_model(
        "Model",
        (
            ResolvedField(
                FieldSpec("items", element=ElementSpec(object)), (0,), semantic
            ),
        ),
    )


@pytest.mark.parametrize(
    "semantic,violation,target",
    [
        (
            DictSemantic(string_semantic(), BooleanSemantic()),
            V.TOO_SHORT,
            CollectionTarget("key"),
        ),
        (
            DictSemantic(BooleanSemantic(), numeric_semantic()),
            V.BELOW_MIN,
            CollectionTarget("value"),
        ),
        (
            DictSemantic(string_semantic(), numeric_semantic()),
            V.BELOW_MIN,
            CollectionTarget("value"),
        ),
        (
            DictSemantic(string_semantic(), numeric_semantic()),
            V.TOO_SHORT,
            CollectionTarget("key"),
        ),
        (
            DictSemantic(string_semantic(), string_semantic()),
            V.TOO_SHORT,
            CollectionTarget("key"),
        ),
        (ListSemantic(numeric_semantic()), V.BELOW_MIN, CollectionTarget("element")),
        (
            TupleSemantic(
                (
                    (BooleanSemantic(), None),
                    (numeric_semantic(), None),
                    (string_semantic(), None),
                )
            ),
            V.BELOW_MIN,
            CollectionTarget("element", 1),
        ),
        (
            TupleSemantic(
                (
                    (BooleanSemantic(), None),
                    (numeric_semantic(), None),
                    (string_semantic(), None),
                )
            ),
            V.TOO_SHORT,
            CollectionTarget("element", 2),
        ),
    ],
)
def test_plans_compatible_collection_target(semantic, violation, target):
    task = plan_violation_task(model_for(semantic), (0,), forced_violation=violation)
    assert task.allowed_violations == (violation,)
    assert task.collection_target == target


def test_default_priority_and_target_agree():
    semantic = DictSemantic(string_semantic(), numeric_semantic())
    task = plan_violation_task(model_for(semantic), (0,))
    assert task.allowed_violations[0] == V.BELOW_MIN
    assert task.collection_target == CollectionTarget("value")


@pytest.mark.parametrize(
    "semantic",
    [
        ListSemantic(
            string_semantic(), length_range=LengthRange(0, 0), is_unique_items=True
        ),
        DictSemantic(
            string_semantic(), numeric_semantic(), length_range=LengthRange(0, 0)
        ),
        TupleSemantic(
            ((string_semantic(), None),),
            length_range=LengthRange(0, 0),
            is_variadic=True,
        ),
    ],
)
def test_empty_only_collections_have_only_size_violation(semantic):
    assert _define_allowed_violation_types(semantic) == (V.TOO_MANY_ITEMS,)
    with pytest.raises(PlanningError) as exc:
        plan_violation_task(model_for(semantic), (0,), forced_violation=V.TOO_SHORT)
    assert exc.value.context["code"] == "invalid_forced_violation"


def test_dictionary_violation_types_are_not_duplicated():
    semantic = DictSemantic(string_semantic(), string_semantic())
    violations = _define_allowed_violation_types(semantic)
    assert len(violations) == len(set(violations))


@pytest.mark.parametrize(
    "semantic,violation",
    [
        (
            DictSemantic(
                EnumSemantic(values=("a", "b")),
                BooleanSemantic(),
                length_range=LengthRange(2, 2),
            ),
            V.TOO_MANY_ITEMS,
        ),
        (
            ListSemantic(
                BooleanSemantic(), length_range=LengthRange(2, 2), is_unique_items=True
            ),
            V.TOO_MANY_ITEMS,
        ),
        (
            ListSemantic(
                BooleanSemantic(), length_range=LengthRange(0, 1), is_unique_items=True
            ),
            V.DUPLICATE,
        ),
        (TupleSemantic(((string_semantic(), None),)), V.TOO_MANY_ITEMS),
        (DictSemantic(string_semantic(), BooleanSemantic()), V.BELOW_MIN),
    ],
)
def test_impossible_or_unsupported_explicit_target_is_rejected(semantic, violation):
    with pytest.raises(PlanningError) as exc:
        plan_violation_task(model_for(semantic), (0,), forced_violation=violation)
    assert exc.value.context["code"] == "invalid_forced_violation"
