import pytest
from semantic_factories import numeric_semantic, string_semantic

from conformly._internal.parser import ElementSpec, FieldSpec
from conformly._internal.planner import PlannedTask
from conformly._internal.planner.field import (
    _VIOLATION_PRIORITY,
    _is_extra_field,
    plan_violation_task,
)
from conformly._internal.resolver import ResolvedField, ResolvedModel
from conformly._internal.resolver.resolve import _build_indexes
from conformly._internal.resolver.semantics import (
    ObjectSemantic,
)
from conformly._internal.types import (
    INT_MAX,
    INT_MIN,
    UNSET,
    FieldPath,
    Range,
    ViolationType,
)
from conformly.exceptions import PlanningError, ResolutionError

# ===== TESTS for plan_violation_task() =====


city_field = ResolvedField(
    field_spec=FieldSpec(
        name="city", element=ElementSpec(str, ()), default=UNSET, nullable=False
    ),
    path=(2, 0, 0),
    semantic=string_semantic(
        min_length=0, max_length=None, pattern=None, has_constraints=False
    ),
)

zip_field = ResolvedField(
    field_spec=FieldSpec(
        name="zip", element=ElementSpec(str, ()), default=UNSET, nullable=False
    ),
    path=(2, 0, 1),
    semantic=string_semantic(
        min_length=0, max_length=120, pattern=None, has_constraints=True
    ),
)

second_nested = ResolvedModel("Address", (city_field, zip_field))

address_field = ResolvedField(
    field_spec=FieldSpec(
        name="address", element=ElementSpec(object, ()), default=UNSET, nullable=False
    ),
    path=(2, 0),
    semantic=ObjectSemantic(),
    nested_model=second_nested,
)

phone_field = ResolvedField(
    field_spec=FieldSpec(
        name="phone", element=ElementSpec(str, ()), default=UNSET, nullable=True
    ),
    path=(2, 1),
    semantic=string_semantic(
        min_length=0, max_length=15, pattern=None, has_constraints=False
    ),
)

first_nested = ResolvedModel("Profile", (address_field, phone_field))

name_field = ResolvedField(
    field_spec=FieldSpec(
        name="name", element=ElementSpec(str, ()), default=UNSET, nullable=False
    ),
    path=(0,),
    semantic=string_semantic(
        min_length=0, max_length=None, pattern=None, has_constraints=True
    ),
)

age_field = ResolvedField(
    field_spec=FieldSpec(
        name="age", element=ElementSpec(int, ()), default=UNSET, nullable=False
    ),
    path=(1,),
    semantic=numeric_semantic(
        valid_range=Range(18, 120),
        invalid_ranges=(Range(INT_MIN, 17), Range(121, INT_MAX)),
    ),
)

profile_field = ResolvedField(
    field_spec=FieldSpec(
        name="profile", element=ElementSpec(object, ()), default=UNSET, nullable=False
    ),
    path=(2,),
    semantic=ObjectSemantic(),
    nested_model=first_nested,
)


@pytest.fixture
def base_model() -> ResolvedModel:
    model = ResolvedModel("User", (name_field, age_field, profile_field))
    _build_indexes(model)
    return model


@pytest.mark.parametrize(
    "path, expected",
    [
        ((0,), PlannedTask((0,), ())),
        ((1,), PlannedTask((1,), (ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX))),
        ((2, 1), PlannedTask((2, 1), (ViolationType.TOO_LONG,))),
        ((2, 0, 0), PlannedTask((2, 0, 0), ())),
    ],
)
def test_plan_violation_task_valid(
    base_model: ResolvedModel, path: FieldPath, expected: PlannedTask
) -> None:
    assert plan_violation_task(base_model, path) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        ((0,), PlannedTask((0,), (ViolationType.TYPE_MISMATCH,))),
        (
            (1,),
            PlannedTask(
                (1,),
                (
                    ViolationType.TYPE_MISMATCH,
                    ViolationType.BELOW_MIN,
                    ViolationType.ABOVE_MAX,
                ),
            ),
        ),
        (
            (2, 1),
            PlannedTask(
                (2, 1),
                (
                    ViolationType.TYPE_MISMATCH,
                    ViolationType.TOO_LONG,
                ),
            ),
        ),
        ((2, 0, 0), PlannedTask((2, 0, 0), (ViolationType.TYPE_MISMATCH,))),
    ],
)
def test_plan_violation_task_allow_type_mismatch(
    base_model: ResolvedModel, path: FieldPath, expected: PlannedTask
) -> None:
    assert plan_violation_task(base_model, path, True) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        ((0,), PlannedTask((0,), (ViolationType.MISSING_FIELD,))),
        (
            (1,),
            PlannedTask(
                (1,),
                (
                    ViolationType.MISSING_FIELD,
                    ViolationType.BELOW_MIN,
                    ViolationType.ABOVE_MAX,
                ),
            ),
        ),
        (
            (2, 1),
            PlannedTask(
                (2, 1),
                (
                    ViolationType.MISSING_FIELD,
                    ViolationType.TOO_LONG,
                ),
            ),
        ),
        ((2, 0, 0), PlannedTask((2, 0, 0), (ViolationType.MISSING_FIELD,))),
    ],
)
def test_plan_violation_task_allow_structural_violations(
    base_model: ResolvedModel, path: FieldPath, expected: PlannedTask
) -> None:
    assert plan_violation_task(base_model, path, False, True) == expected


@pytest.mark.parametrize(
    "path",
    [(3,), (2, 2), (2, 0, 2)],
)
def test_plan_violation_task_valid_extra_field(
    base_model: ResolvedModel, path: FieldPath
) -> None:
    assert plan_violation_task(base_model, path, False, True) == PlannedTask(
        path, (ViolationType.EXTRA_FIELD,)
    )


@pytest.mark.parametrize("path", [(3,), (0, 1), (2, 2), (2, 1, 4)])
def test_plan_violation_task_invalid(
    base_model: ResolvedModel, path: FieldPath
) -> None:
    with pytest.raises((IndexError, ValueError, ResolutionError, PlanningError)):
        plan_violation_task(base_model, path)


def test_plan_violation_task_raises_for_type_mismatch_nested_models(
    base_model: ResolvedModel,
) -> None:
    with pytest.raises(PlanningError):
        plan_violation_task(base_model, (2,), True)


@pytest.mark.parametrize("path", [(5,), (2, 5), (2, 0, 4)])
def test_plan_violation_task_invalid_extra_field(
    base_model: ResolvedModel, path: FieldPath
) -> None:
    with pytest.raises((IndexError, ValueError, ResolutionError)):
        plan_violation_task(base_model, path, False, True)


# ===== TESTS for _is_extra_field() =====


def test_is_extra_field_no_path(base_model: ResolvedModel) -> None:
    assert not _is_extra_field(base_model, ())


def test_is_extra_field_path_longer_than_extra(base_model: ResolvedModel) -> None:
    assert not _is_extra_field(base_model, (4,))


def test_is_extra_field_path_longer_than_extra_nester(
    base_model: ResolvedModel,
) -> None:
    assert not _is_extra_field(base_model, (2, 5))


# ===== TESTS for violation priority =====


def test_all_violation_types_in_priority() -> None:
    priority_set = set(_VIOLATION_PRIORITY)
    all_violations = set(ViolationType)

    missing = all_violations - priority_set
    assert not missing, f"ViolationType(s) not in _VIOLATION_PRIORITY: {missing}"


def test_first_violation_is_highest_priority(base_model: ResolvedModel) -> None:
    test_cases = [
        ((0,), True, True, ViolationType.MISSING_FIELD),
        ((1,), True, True, ViolationType.MISSING_FIELD),
        ((2, 1), True, True, ViolationType.MISSING_FIELD),
    ]

    for path, allow_type, allow_struct, expected_first in test_cases:
        task = plan_violation_task(
            base_model,
            path,
            allow_type_mismatch=allow_type,
            allow_structural_violations=allow_struct,
        )
        assert task.allowed_violations[0] == expected_first, (
            f"Field {path}: expected {expected_first}, got {task.allowed_violations[0]}"
        )


def test_violations_sorted_by_priority(base_model: ResolvedModel) -> None:
    task = plan_violation_task(
        base_model,
        path=(1,),
        allow_type_mismatch=True,
        allow_structural_violations=True,
    )

    expected = (
        ViolationType.MISSING_FIELD,
        ViolationType.TYPE_MISMATCH,
        ViolationType.BELOW_MIN,
        ViolationType.ABOVE_MAX,
    )

    assert task.allowed_violations == expected
