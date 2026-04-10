from dataclasses import dataclass
import random

from rstr import Rstr


@dataclass(frozen=True)
class GenerationContext:
    rng: random.Random
    rstr: Rstr
    seed: int | None = None


def create_context(seed: int | None = None) -> GenerationContext:
    rng = random.Random(seed) if seed else random.Random()
    return GenerationContext(rng=rng, rstr=Rstr(rng), seed=seed)
