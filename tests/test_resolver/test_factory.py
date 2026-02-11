import pytest
from conformly.resolver.semantics.factory import create_minimal_semantic
from conformly.types import FieldKind


@pytest.mark.parametrize("kind", list(FieldKind))
def test_minimal_semantic_factory(kind: FieldKind) -> None:
    assert create_minimal_semantic(kind).kind == kind
