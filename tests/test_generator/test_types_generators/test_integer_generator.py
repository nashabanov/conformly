import pytest

from conformly._internal.generator.context import GenerationContext
from conformly._internal.generator.types.integer import (
    _generate_invalid_integer,
    generate_value,
)
from conformly._internal.resolver.semantics.numeric import NumericSemantic
from conformly._internal.types import INT_MAX, INT_MIN, FieldKind, Range, ViolationType
from conformly.exceptions import GenerationError

int_semantic_10_20 = NumericSemantic(
    kind=FieldKind.INTEGER,
    valid_range=Range(10, 20),
    invalid_ranges=(
        Range(-100, 9),
        Range(21, 100),
    ),
    has_constraints=True,
)

int_semantic_ge5 = NumericSemantic(
    kind=FieldKind.INTEGER,
    valid_range=Range(5, INT_MAX),
    invalid_ranges=(Range(-50, 4),),
    has_constraints=True,
)

int_semantic_le100 = NumericSemantic(
    kind=FieldKind.INTEGER,
    valid_range=Range(INT_MIN, 100),
    invalid_ranges=(Range(101, 200),),
    has_constraints=True,
)

int_semantic_multiple_of = NumericSemantic(
    kind=FieldKind.INTEGER,
    valid_range=Range(10, 20),
    invalid_ranges=(Range(-100, 9), Range(21, 100)),
    has_constraints=True,
    multiple_of=2,
)


# ===== TESTS FOR _generate_invalid_integer() =====


@pytest.mark.parametrize(
    "semantic, violation",
    [
        (int_semantic_10_20, ViolationType.BELOW_MIN),
        (int_semantic_10_20, ViolationType.ABOVE_MAX),
        (int_semantic_ge5, ViolationType.BELOW_MIN),
        (int_semantic_le100, ViolationType.ABOVE_MAX),
        (int_semantic_multiple_of, ViolationType.NOT_MULTIPLE),
    ],
)
def test_generate_invalid_integer(
    semantic: NumericSemantic, violation: ViolationType, ctx: GenerationContext
) -> None:
    for _ in range(30):
        val = _generate_invalid_integer(ctx, semantic, violation)
        assert (
            val < semantic.valid_range.min_value or val > semantic.valid_range.max_value
        )
        if violation == ViolationType.BELOW_MIN:
            assert val < semantic.valid_range.min_value

        if violation == ViolationType.ABOVE_MAX:
            assert val > semantic.valid_range.max_value

        if violation == ViolationType.NOT_MULTIPLE:
            assert semantic.multiple_of is not None
            assert val % int(semantic.multiple_of) != 0


def test_generate_invalid_integer_no_matching_range_raises(
    ctx: GenerationContext,
) -> None:
    semantic = NumericSemantic(
        kind=FieldKind.INTEGER,
        valid_range=Range(0.0, 10.0),
        invalid_ranges=(Range(11.0, 20.0),),
        has_constraints=True,
    )

    with pytest.raises(GenerationError):
        _generate_invalid_integer(ctx, semantic, ViolationType.BELOW_MIN)


# ===== TESTS FOR generate_value() =====


@pytest.mark.parametrize(
    "semantic, violation",
    [
        (int_semantic_10_20, None),
        (int_semantic_10_20, None),
        (int_semantic_ge5, None),
        (int_semantic_le100, None),
        (int_semantic_10_20, ViolationType.BELOW_MIN),
        (int_semantic_10_20, ViolationType.ABOVE_MAX),
        (int_semantic_ge5, ViolationType.BELOW_MIN),
        (int_semantic_le100, ViolationType.ABOVE_MAX),
        (int_semantic_multiple_of, None),
    ],
)
def test_generate(
    semantic: NumericSemantic, violation: ViolationType | None, ctx: GenerationContext
) -> None:
    if not violation:
        val = generate_value(ctx, semantic, violation)
        if semantic.multiple_of is not None:
            assert val % semantic.multiple_of == 0
        assert semantic.valid_range.min_value <= val <= semantic.valid_range.max_value
    else:
        for _ in range(30):
            val = generate_value(ctx, semantic, violation)
            assert (
                val < semantic.valid_range.min_value
                or val > semantic.valid_range.max_value
            )


def test_generate_value_raises_on_ranges_conflict_with_multiple(
    ctx: GenerationContext,
) -> None:
    semantic = NumericSemantic(
        kind=FieldKind.INTEGER,
        valid_range=Range(10, 20),
        invalid_ranges=(Range(-100, 9), Range(21, 100)),
        has_constraints=True,
        multiple_of=21,
    )
    with pytest.raises(GenerationError):
        generate_value(ctx, semantic, None)
