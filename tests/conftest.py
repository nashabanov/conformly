import pytest

from conformly._internal.generator import GenerationContext, create_context


@pytest.fixture
def ctx() -> GenerationContext:
    return create_context()


@pytest.fixture
def ctx_deterministic() -> GenerationContext:
    return create_context(42)
