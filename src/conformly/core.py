from typing import Any

from .generator import generate_invalid, generate_valid
from .parsing import parse_model
from .planner import PlannedTask, plan_violation_task, select_paths
from .resolver import ResolvedModel, resolve_model
from .specs import ModelSpec
from .types import CasesStrategy, CaseStrategy


def _ensure_model_or_spec(
    model_or_spec: ModelSpec | ResolvedModel | type,
) -> ResolvedModel:
    if isinstance(model_or_spec, ResolvedModel):
        return model_or_spec

    if isinstance(model_or_spec, ModelSpec):
        return resolve_model(model_or_spec)

    return resolve_model(parse_model(model_or_spec))


def _plan_tasks(
    model: ResolvedModel,
    *,
    strategy: CasesStrategy,
    allow_all: bool,
    count: int | None = None,
) -> list[PlannedTask]:
    paths = select_paths(
        model,
        strategy=strategy,
        allow_all=allow_all,
        count=count or 1,
    )
    return [plan_violation_task(model, path) for path in paths]


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
               - "field_name": violate a specific field
                 (use dotted paths for nested fields e.g. strategy="user.email")

    Returns:
        A single dictionary representing the instance.

    Raises:
        ValueError: If no constrained fields exist (for valid=False).
    """
    model = _ensure_model_or_spec(model_or_spec)

    if valid:
        if strategy != "first":
            raise ValueError("Strategy is only applicable when valid=False")
        return generate_valid(model)

    if strategy == "all":
        raise ValueError(
            "'all' strategy is not supported in 'case()' — use 'cases()' instead"
        )

    task = _plan_tasks(model, strategy=strategy, allow_all=False, count=1)[0]
    return generate_invalid(model, task)


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
                 (use dotted paths for nested fields e.g. strategy="user.email")
        count: Number of cases to generate (ignored if strategy="all").

    Returns:
        A list of dictionaries.

    Raises:
        ValueError: If no constrained fields exist (for valid=False).
    """
    if count < 1:
        raise ValueError("count must be >= 1")

    model = _ensure_model_or_spec(model_or_spec)

    if valid:
        if strategy != "first":
            raise ValueError("Strategy is only applicable when valid=False")
        return [generate_valid(model) for _ in range(count)]

    if strategy == "all":
        tasks = _plan_tasks(model, strategy="all", allow_all=True)

    else:
        tasks = _plan_tasks(model, strategy=strategy, allow_all=False, count=count)

    return [generate_invalid(model, task) for task in tasks]
