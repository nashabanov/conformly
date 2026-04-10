import pytest

from conformly._internal.generator.context import GenerationContext
from conformly._internal.generator.orchestration import (
    generate_field,
    generate_invalid,
    generate_valid,
)
from conformly._internal.parser import FieldSpec
from conformly._internal.planner import PlannedTask
from conformly._internal.resolver import ResolvedField, ResolvedModel
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
    ViolationType,
)

simple_string_field = ResolvedField(
    field_spec=FieldSpec(name="name", field_type=str, default=UNSET, nullable=False),
    path=(0,),
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, 15), None, True),
)

default_string_field = ResolvedField(
    field_spec=FieldSpec(
        name="city", field_type=str, default="Palo Alto", nullable=False
    ),
    path=(0, 1),
    semantic=StringSemantic(FieldKind.STRING, LengthRange(5, 40), None, True),
)

optional_string_field = ResolvedField(
    field_spec=FieldSpec(
        name="description", field_type=str, default="simple description", nullable=True
    ),
    path=(3,),
    semantic=StringSemantic(FieldKind.STRING, LengthRange(0, 60), None, True),
)

bool_field = ResolvedField(
    field_spec=FieldSpec(
        name="is_admin", field_type=bool, default=UNSET, nullable=False
    ),
    path=(4,),
    semantic=BooleanSemantic(),
)

nested_model = ResolvedModel(
    name="Profile",
    fields=(
        ResolvedField(
            field_spec=FieldSpec(
                name="address", field_type=str, default=UNSET, nullable=True
            ),
            path=(1, 0),
            semantic=StringSemantic(FieldKind.STRING, LengthRange(5, 25), None, True),
        ),
        ResolvedField(
            field_spec=FieldSpec(
                name="age", field_type=int, default=UNSET, nullable=False
            ),
            path=(1, 1),
            semantic=NumericSemantic(
                kind=FieldKind.INTEGER,
                valid_range=Range(18, 120),
                invalid_ranges=(
                    Range(INT_MIN, 17),
                    Range(121, INT_MAX),
                ),
                has_constraints=True,
            ),
        ),
    ),
)

nested_field = ResolvedField(
    field_spec=FieldSpec(
        name="profile", field_type=object, default=UNSET, nullable=False
    ),
    path=(1,),
    nested_model=nested_model,
    semantic=ObjectSemantic(),
)


# ===== TESTS for generate_field() =====


def test_generate_field_valid_simple_string(ctx: GenerationContext) -> None:
    field_value = generate_field(ctx, simple_string_field, None)
    assert isinstance(field_value, str)
    assert len(field_value) <= 15


def test_generate_field_invalid_simple_string(ctx: GenerationContext) -> None:
    field_value = generate_field(ctx, simple_string_field, (ViolationType.TOO_LONG,))
    assert isinstance(field_value, str)
    assert len(field_value) > 15


def test_generate_field_valid_bool(ctx: GenerationContext) -> None:
    value = generate_field(ctx, bool_field, None)
    assert isinstance(value, bool)


def test_generate_field_valid_default(ctx: GenerationContext) -> None:
    assert generate_field(ctx, default_string_field, None) == "Palo Alto"


def test_generate_field_invalid_default(ctx: GenerationContext) -> None:
    field_value = generate_field(
        ctx, default_string_field, (ViolationType.TOO_SHORT, ViolationType.TOO_LONG)
    )
    assert isinstance(field_value, str)
    assert len(field_value) < 5 or len(field_value) > 40


def test_generate_field_valid_optional(ctx: GenerationContext) -> None:
    assert generate_field(ctx, optional_string_field, None) is None


def test_generate_field_invalid_optional(ctx: GenerationContext) -> None:
    field_value = generate_field(ctx, optional_string_field, (ViolationType.TOO_LONG,))
    assert isinstance(field_value, str)
    assert len(field_value) > 60


def test_generate_field_invalid_type_mismatch(ctx: GenerationContext) -> None:
    field_value = generate_field(
        ctx, simple_string_field, (ViolationType.TYPE_MISMATCH,)
    )
    assert not isinstance(field_value, str) or field_value == "__type_mismatch__"


def test_generate_missing_field(ctx: GenerationContext) -> None:
    assert (
        generate_field(ctx, simple_string_field, (ViolationType.MISSING_FIELD,))
        is UNSET
    )


# ===== TESTS for generate_invalid() =====


def test_generate_invalid_flat(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, bool_field))
    task = PlannedTask(path=(0,), allowed_violations=(ViolationType.TOO_LONG,))

    result = generate_invalid(ctx, model, task)

    assert isinstance(result["name"], str)
    assert len(result["name"]) > 15
    assert isinstance(result["is_admin"], bool)


def test_generate_invalid_empty_violations(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, bool_field))
    task = PlannedTask(path=(0,), allowed_violations=())

    with pytest.raises(ValueError):
        generate_invalid(ctx, model, task)


def test_generate_invalid_nested(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, nested_field))
    task = PlannedTask(
        path=(1, 1),
        allowed_violations=(ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
    )

    result = generate_invalid(ctx, model, task)

    assert isinstance(result["name"], str)
    assert len(result["name"]) <= 15
    assert isinstance(result["profile"], dict)
    assert result["profile"]["address"] is None
    assert isinstance(result["profile"]["age"], int)
    assert result["profile"]["age"] < 18 or result["profile"]["age"] > 120


def test_generate_invalid_path_into_non_nested_field(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field,))
    task = PlannedTask((0, 1), (ViolationType.BELOW_MIN,))

    with pytest.raises(ValueError):
        generate_invalid(ctx, model, task)


def test_generate_invalid_ureacheble_index(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field,))
    task = PlannedTask((2,), (ViolationType.ABOVE_MAX,))

    with pytest.raises(IndexError):
        generate_invalid(ctx, model, task)


def test_generate_invalid_ureacheble_index_nested(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, nested_field))
    task = PlannedTask(
        path=(1, 4),
        allowed_violations=(ViolationType.BELOW_MIN, ViolationType.ABOVE_MAX),
    )

    with pytest.raises(IndexError):
        generate_invalid(ctx, model, task)


def test_generate_invalid_skip_missing_field(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, nested_field))
    task = PlannedTask((0,), (ViolationType.MISSING_FIELD,))
    assert len(generate_invalid(ctx, model, task)) == 1


def test_generate_invalid_skip_missing_field_nested(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, nested_field))
    task = PlannedTask((1, 0), (ViolationType.MISSING_FIELD,))
    assert len(generate_invalid(ctx, model, task)["profile"]) == 1


def test_generate_invalid_skip_missing_field_with_nested_model(
    ctx: GenerationContext,
) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, nested_field))
    task = PlannedTask((1,), (ViolationType.MISSING_FIELD,))
    assert len(generate_invalid(ctx, model, task)) == 1


def test_generate_invalid_extra_field(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, nested_field))
    task = PlannedTask((2,), (ViolationType.EXTRA_FIELD,))
    assert len(generate_invalid(ctx, model, task)) == 3


def test_generate_invalid_extra_field_nested(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, nested_field))
    task = PlannedTask((1, 2), (ViolationType.EXTRA_FIELD,))
    assert len(generate_invalid(ctx, model, task)["profile"]) == 3


# ===== TESTS for generate_valid() =====


def test_generate_valid_flat(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, bool_field))

    result = generate_valid(ctx, model)

    assert isinstance(result, dict)
    assert result.keys() == {"name", "is_admin"}
    assert isinstance(result["name"], str)
    assert len(result["name"]) <= 15
    assert isinstance(result["is_admin"], bool)


def test_generate_valid_nested(ctx: GenerationContext) -> None:
    model = ResolvedModel(name="User", fields=(simple_string_field, nested_field))

    result = generate_valid(ctx, model)

    assert isinstance(result, dict)
    assert result.keys() == {"name", "profile"}
    assert isinstance(result["name"], str)
    assert len(result["name"]) <= 15
    assert isinstance(result["profile"], dict)

    nested_result = result["profile"]

    assert nested_result["address"] is None
    assert isinstance(nested_result["age"], int)
    assert nested_result["age"] <= 120 and nested_result["age"] >= 18
