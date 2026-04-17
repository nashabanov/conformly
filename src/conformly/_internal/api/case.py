from typing import Any

from ._errors import api_error
from ._utils import ensure_model_or_spec, plan_tasks
from .path import PathSelector

from conformly._internal.generator.context import create_context
from conformly._internal.generator.orchestration import generate_invalid, generate_valid
from conformly._internal.parser import ModelSpec
from conformly._internal.types import CaseStrategy


def case(
    model_or_spec: ModelSpec | type,
    *,
    valid: bool = True,
    seed: int | None = None,
    strategy: CaseStrategy | PathSelector = "first",
    allow_type_mismatch: bool = False,
) -> dict[str, Any]:
    """
    Generate a single example of a model.

    Note:
        Violation types are chosen deterministically based on priority
        (Structural > Type > Semantic) to ensure reproducible test failures.

    Args:
        model_or_spec:
            Model class (e.g. dataclass, Pydantic)
            or parsed ModelSpec/ResolvedModel.

        valid:
            If True, generate a valid instance.
            If False, generate an invalid one.

        seed:
            Random seed for reproducible generation.
            - `None` (default): Use system randomness (different output each run).
            - `int`: Initialize RNG with fixed seed (same output for same seed).

        strategy:
            Define which field to violate when valid=False.

            - "first":
                violate the first constrained field (default)

            - "random": violate a random constrained field

            - "field_name":
                violate a specific field using a dotted path
                (e.g. strategy="user.email")

            - "field_name::violation":
                violate a specific field with specific type
                (e.g. strategy="user.profile::below_min")

            - PathSelector DSL:
                path("user.email").violate(V.TOO_SHORT)

        allow_type_mismatch:
            If True fields could be type mismatched.
            Availiable only when valid=False.

    Returns:
        A dictionary representing the instance.
    """
    model = ensure_model_or_spec(model_or_spec)

    ctx = create_context(seed)

    if valid:
        if allow_type_mismatch:
            raise api_error(
                "Type mismatch is only available for invalid generation",
                code="invalid_flag_for_valid",
                flag="allow_type_mismatch",
            )

        if strategy != "first":
            raise api_error(
                "Strategy selection is only applicable when valid=False",
                code="invalid_strategy_for_valid",
                strategy=strategy,
            )

        return generate_valid(ctx, model)

    if strategy == "all":
        raise api_error(
            "The 'all' strategy is not supported in 'case()' — use 'cases()' instead",
            code="unsupported_strategy",
            function="case",
            strategy=strategy,
        )

    task = plan_tasks(
        model,
        ctx=ctx,
        strategy=strategy,
        allow_all=False,
        count=1,
        allow_type_mismatch=allow_type_mismatch,
    )[0]
    return generate_invalid(ctx, model, task)
