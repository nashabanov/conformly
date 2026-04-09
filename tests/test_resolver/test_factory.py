import pytest

from conformly._internal.types import FieldKind
from conformly.resolver.semantics.factory import create_minimal_semantic


@pytest.mark.parametrize("kind", list(FieldKind))
def test_minimal_semantic_factory(kind: FieldKind) -> None:
    assert create_minimal_semantic(kind).kind == kind
