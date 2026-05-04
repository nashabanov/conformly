from conformly._internal.parser import ElementSpec, FieldSpec
from conformly._internal.planner.session import _filter_candidate_paths
from conformly._internal.resolver.models import ResolvedField, ResolvedModel
from conformly._internal.resolver.resolve import _build_indexes
from conformly._internal.resolver.semantics import (
    BooleanSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly._internal.types import (
    INT_MAX,
    INT_MIN,
    UNSET,
    FieldKind,
    LengthRange,
    Range,
)

resolved_model = ResolvedModel(
    name="User",
    fields=(
        ResolvedField(
            field_spec=FieldSpec(
                name="name",
                element=ElementSpec(str, ()),
                default=UNSET,
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
                element=ElementSpec(int, ()),
                default=UNSET,
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
                element=ElementSpec(bool, ()),
                default=True,
                nullable=False,
            ),
            path=(2,),
            semantic=BooleanSemantic(),
        ),
        ResolvedField(
            field_spec=FieldSpec(
                name="profile",
                element=ElementSpec(object, ()),
                default=UNSET,
                nullable=False,
            ),
            path=(3,),
            semantic=ObjectSemantic(),
            nested_model=ResolvedModel(
                name="Profile",
                fields=(
                    ResolvedField(
                        field_spec=FieldSpec(
                            name="is_blocked",
                            element=ElementSpec(bool, ()),
                            default=False,
                            nullable=False,
                        ),
                        path=(3, 0),
                        semantic=BooleanSemantic(),
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
