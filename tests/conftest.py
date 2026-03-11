from random import Random

import pytest

from conformly.generator.context import GenerationContext


@pytest.fixture
def ctx() -> GenerationContext:
    return GenerationContext(rng=Random())


@pytest.fixture
def ctx_deterministic() -> GenerationContext:
    return GenerationContext(rng=Random(42), seed=42)
