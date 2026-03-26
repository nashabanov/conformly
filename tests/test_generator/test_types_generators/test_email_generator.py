from conformly.generator.context import GenerationContext
from conformly.generator.types.email import INVALID_FORMATS, generate_value
from conformly.resolver.semantics.string import LengthRange, StringSemantic
from conformly.types import FieldKind, ViolationType


def test_generate_valid_email_no_constraints(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    result = generate_value(ctx, semantic, violation=None)

    assert "@" in result
    assert "." in result.split("@")[1]
    assert len(result) >= 7


def test_generate_valid_email_with_min_length(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=20, max_length=None),
        pattern=None,
        has_constraints=True,
    )

    result = generate_value(ctx, semantic, violation=None)

    assert len(result) >= 20
    assert "@" in result


def test_generate_invalid_email_too_short(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=15, max_length=None),
        pattern=None,
        has_constraints=True,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_SHORT)

    assert len(result) < 15


def test_generate_valid_email_domain_fallback(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=500, max_length=600),
        pattern=None,
        has_constraints=True,
    )

    result = generate_value(ctx, semantic, violation=None)

    assert "@" in result
    assert "." in result.split("@")[1]


def test_generate_valid_email_with_max_length(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=10, max_length=15),
        pattern=None,
        has_constraints=True,
    )

    result = generate_value(ctx, semantic, violation=None)

    assert len(result) >= 10
    assert len(result) <= 15, f"Expected <= 15, got {len(result)}: {result!r}"
    assert "@" in result


def test_generate_valid_email_final_padding(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=25, max_length=30),
        pattern=None,
        has_constraints=True,
    )

    for _ in range(50):
        result = generate_value(ctx, semantic, violation=None)
        assert len(result) >= 25, f"Padding failed: {result!r} (len={len(result)})"
        assert "@" in result


def test_generate_invalid_email_too_short_with_min(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=15, max_length=None),
        pattern=None,
        has_constraints=True,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_SHORT)

    assert len(result) < 15, f"Expected < 15, got {len(result)}: {result!r}"


def test_generate_invalid_email_too_short_edge_cases(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=True,
    )
    result = generate_value(ctx, semantic, violation=ViolationType.TOO_SHORT)
    assert result == ""

    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=1, max_length=None),
        pattern=None,
        has_constraints=True,
    )
    result = generate_value(ctx, semantic, violation=ViolationType.TOO_SHORT)
    assert result == "a"


def test_generate_invalid_email_too_long_with_max(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=5, max_length=10),
        pattern=None,
        has_constraints=True,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_LONG)

    assert len(result) > 10, f"Expected > 10, got {len(result)}: {result!r}"
    assert "@" in result


def test_generate_invalid_email_too_long_no_max(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=5, max_length=None),
        pattern=None,
        has_constraints=True,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.TOO_LONG)

    assert len(result) > 70
    assert result.count("a") > 60


def test_generate_invalid_email_pattern_mismatch(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    results = [
        generate_value(ctx, semantic, violation=ViolationType.NOT_EMAIL)
        for _ in range(20)
    ]

    for result in results:
        assert result in INVALID_FORMATS


def test_generate_invalid_email_unknown_violation(ctx: GenerationContext) -> None:
    semantic = StringSemantic(
        kind=FieldKind.EMAIL,
        length_range=LengthRange(min_length=0, max_length=None),
        pattern=None,
        has_constraints=False,
    )

    result = generate_value(ctx, semantic, violation=ViolationType.NOT_MULTIPLE)

    assert result == "invalid-email"
