import pytest

from conformly.generator.context import GenerationContext, create_context


@pytest.fixture
def ctx() -> GenerationContext:
    return create_context()


@pytest.fixture
def ctx_deterministic() -> GenerationContext:
    return create_context(42)
