import pytest

from conformly.planner import PlannedTask
from conformly.planner.plan import define_string_violations
from conformly.resolver.semantics import StringSemantic

# ===== TESTS for define_string_violations() =====


@pytest.mark.parametrize(
    "semantic, expected",
    [
        (),
        (),
        (),
        (),
        (),
    ],
)
def test_define_string_violations(
    semantic: StringSemantic, expected: PlannedTask
) -> None:
    task = define_string_violations(semantic)
    assert task == expected
