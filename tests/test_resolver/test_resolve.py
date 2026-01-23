import pytest

from conformly.constraints import (
    Constraint,
    MaxLength,
    MinLength,
    Pattern,
)
from conformly.resolver.resolve import (
    create_string_semantic,
)
from conformly.resolver.semantics import StringSemantic
from conformly.resolver.semantics.string import LengthRange
from conformly.types import FieldKind

# ===== TESTS for create_string_semantic() =====


@pytest.mark.parametrize(
    "constraints, expected",
    [
        (
            [MinLength(5), MaxLength(50), Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 50, True, True),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [MinLength(3)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(3, None, True, False),
                pattern=None,
            ),
        ),
        (
            [MaxLength(100)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 100, False, True),
                pattern=None,
            ),
        ),
        (
            [Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None, False, False),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [MinLength(5), Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None, True, False),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [MaxLength(15), Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 15, False, True),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None, False, False),
                pattern=None,
            ),
        ),
        (
            [MinLength(0)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, None, True, False),
                pattern=None,
            ),
        ),
        (
            [MaxLength(0)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 0, False, True),
                pattern=None,
            ),
        ),
        (
            [MinLength(5), MaxLength(50), Pattern(r"[a-z]+")],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, 50, True, True),
                pattern=r"[a-z]+",
            ),
        ),
        (
            [MinLength(2), MinLength(5)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(5, None, has_min=True, has_max=False),
                pattern=None,
            ),
        ),
        (
            [MaxLength(20), MaxLength(10)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(0, 10, has_min=False, has_max=True),
                pattern=None,
            ),
        ),
        (
            [MinLength(3), MinLength(7), MaxLength(15), MaxLength(10)],
            StringSemantic(
                kind=FieldKind.STRING,
                length_range=LengthRange(7, 10, has_min=True, has_max=True),
                pattern=None,
            ),
        ),
    ],
)
def test_create_valid_string_semantic(
    constraints: list[Constraint], expected: StringSemantic
) -> None:
    semantic = create_string_semantic(constraints)
    assert semantic == expected


def test_create_invalid_string_semantic() -> None:
    with pytest.raises(ValueError):
        create_string_semantic([MinLength(10), MaxLength(3)])
        create_string_semantic([Pattern(r"\d+"), Pattern(r"[0-9]{3}")])


# ===== TESTS for get_numeric_bounds() =====
