from typing import Any, Literal

from .parsing import parse_model
from .specs import ModelSpec

CaseStrategy = Literal["first", "random"] | str
CasesStrategy = Literal["first", "random", "all"] | str


def _ensure_model_or_spec(model_or_spec: ModelSpec | type) -> ModelSpec:
    if isinstance(model_or_spec, type):
        return parse_model(model_or_spec)
    return model_or_spec


# ===== case =====
def case(
    model_or_spec: ModelSpec | type,
    *,
    valid: bool = True,
    strategy: CaseStrategy = "first",
) -> dict[str, Any]:
    """
    Generate a single example.

    Args:
        model_or_spec: Model class (e.g. dataclass, Pydantic) or parsed ModelSpec.
        valid: If True, generate a valid instance. If False, generate an invalid one.
        strategy: How to choose which field to violate when valid=False.
               - "first": violate the first constrained field (default)
               - "random": violate a random constrained field
               - "field_name": violate a specific field (e.g. strategy="email")

    Returns:
        A single dictionary representing the instance.

    Raises:
        ValueError: If no constrained fields exist (for valid=False).
    """
    ...


# ===== cases =====
def cases(
    model_or_spec: ModelSpec | type,
    *,
    valid: bool = True,
    strategy: CasesStrategy = "first",
    count: int = 1,
) -> list[dict[str, Any]]:
    """
    Generate multiple examples.

    Args:
        model_or_spec: Model class or parsed ModelSpec.
        valid: If True, generate valid instances. If False, generate invalid ones.
        strategy: How to choose fields to violate when valid=False.
               - "first": take the first N constrained fields (default)
               - "random": take N random constrained fields
               - "all": generate one invalid case per constrained field (ignores count)
               - "field_name": generate one case violating a specific field
        count: Number of cases to generate (ignored if strategy="all").

    Returns:
        A list of dictionaries.

    Raises:
        ValueError: If no constrained fields exist (for valid=False).
    """
    ...
