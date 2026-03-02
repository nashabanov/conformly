from conformly.planner.plan_session import _filter_candidate_paths
from conformly.resolver.field import ResolvedField
from conformly.resolver.model import ResolvedModel
from conformly.resolver.resolve import _build_indexes
from conformly.resolver.semantics import (
    BooleanSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly.specs import FieldSpec
from conformly.types import _UNSET, INT_MAX, INT_MIN, FieldKind, LengthRange, Range

resolved_model = ResolvedModel(
    name="User",
    fields=(
        ResolvedField(
            field_spec=FieldSpec(
                name="name",
                type=str,
                default=_UNSET,
                nullable=False,
            ),
            path=(0,),
            semantic=StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(3, None),
                pattern=None,
                has_constraints=True,
            ),
        ),
        ResolvedField(
            field_spec=FieldSpec(
                name="age",
                type=int,
                default=_UNSET,
                nullable=False,
            ),
            path=(1,),
            semantic=NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(18, 120),
                invalid_ranges=(Range(INT_MIN, 17), Range(121, INT_MAX)),
                has_constraints=True,
            ),
        ),
        ResolvedField(
            field_spec=FieldSpec(
                name="is_admin",
                type=bool,
                default=True,
                nullable=False,
            ),
            path=(2,),
            semantic=BooleanSemantic(FieldKind.BOOLEAN),
        ),
        ResolvedField(
            field_spec=FieldSpec(
                name="profile",
                type=object,
                default=_UNSET,
                nullable=False,
            ),
            path=(3,),
            semantic=ObjectSemantic(FieldKind.OBJECT),
            nested_model=ResolvedModel(
                name="Profile",
                fields=(
                    ResolvedField(
                        field_spec=FieldSpec(
                            name="is_blocked",
                            type=bool,
                            default=False,
                            nullable=False,
                        ),
                        path=(3, 0),
                        semantic=BooleanSemantic(FieldKind.BOOLEAN),
                    ),
                ),
            ),
        ),
    ),
)


def test_gather_constrained_paths_default() -> None:
    _build_indexes(resolved_model)
    assert _filter_candidate_paths(resolved_model) == (
        (0,),
        (1,),
    )


def test_gather_constrained_paths_allow_type_mismatch() -> None:
    _build_indexes(resolved_model)
    assert _filter_candidate_paths(resolved_model, True) == (
        (0,),
        (1,),
        (2,),
        (3, 0),
    )


def test_gather_constrained_paths_allow_structural_violations() -> None:
    _build_indexes(resolved_model)
    assert _filter_candidate_paths(resolved_model, False, True) == (
        (0,),
        (1,),
        (2,),
        (3,),
        (3, 0),
        (3, 1),
        (4,),
    )
