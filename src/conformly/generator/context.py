from dataclasses import dataclass
import random


@dataclass(frozen=True)
class GenerationContext:
    rng: random.Random
    seed: int | None = None


def create_context(seed: int | None = None) -> GenerationContext:
    if seed is None:
        return GenerationContext(rng=random.Random())
    return GenerationContext(rng=random.Random(seed), seed=seed)
