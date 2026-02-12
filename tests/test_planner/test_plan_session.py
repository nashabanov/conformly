from conformly.planner.plan_session import _gather_constrained_paths
from conformly.resolver.field import ResolvedField
from conformly.resolver.model import ResolvedModel
from conformly.resolver.semantics import (
    BooleanSemantic,
    NumericSemantic,
    ObjectSemantic,
    StringSemantic,
)
from conformly.types import INT_MAX, INT_MIN, FieldKind, LengthRange, Range

resolved_model = ResolvedModel(
    name="User",
    fields=(
        ResolvedField(
            name="name",
            path=(0,),
            py_type=str,
            default=None,
            nullable=False,
            semantic=StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(3, None),
                pattern=None,
                has_constraints=True,
            ),
        ),
        ResolvedField(
            name="age",
            path=(1,),
            py_type=int,
            default=None,
            nullable=False,
            semantic=NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(18, 120),
                invalid_ranges=(Range(INT_MIN, 17), Range(121, INT_MAX)),
                has_constraints=True,
            ),
        ),
        ResolvedField(
            name="is_admin",
            path=(2,),
            py_type=bool,
            default=True,
            nullable=False,
            semantic=BooleanSemantic(FieldKind.BOOLEAN),
        ),
        ResolvedField(
            name="profile",
            path=(3,),
            py_type=object,
            default=None,
            nullable=False,
            semantic=ObjectSemantic(FieldKind.OBJECT),
            nested_model=ResolvedModel(
                name="Profile",
                fields=(
                    ResolvedField(
                        name="is_blocked",
                        path=(3, 0),
                        py_type=bool,
                        default=False,
                        nullable=False,
                        semantic=BooleanSemantic(FieldKind.BOOLEAN),
                    ),
                ),
            ),
        ),
    ),
)


def test_gather_constrained_paths_default() -> None:
    assert _gather_constrained_paths(resolved_model) == (
        ((0,), "name"),
        ((1,), "age"),
    )


def test_gather_constrained_paths_allow_type_mismatch() -> None:
    assert _gather_constrained_paths(resolved_model, True) == (
        ((0,), "name"),
        ((1,), "age"),
        ((2,), "is_admin"),
        ((3, 0), "profile.is_blocked"),
    )
