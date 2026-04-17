from typing import Any

from ._errors import api_error
from ._utils import ensure_model_or_spec, plan_tasks
from .path import PathSelector, parse_strategy_input

from conformly._internal.generator.context import create_context
from conformly._internal.generator.orchestration import generate_invalid, generate_valid
from conformly._internal.parser.models import ModelSpec
from conformly._internal.types.strategies import CasesStrategy


def cases(
    model_or_spec: ModelSpec | type,
    *,
    valid: bool = True,
    seed: int | None = None,
    strategy: CasesStrategy | PathSelector = "first",
    count: int = 1,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
) -> list[dict[str, Any]]:
    """
    Generate multiple examples of a model.

    Note:
        Violation types are chosen deterministically based on priority
        (Structural > Type > Semantic) to ensure reproducible test failures.

    Args:
        model_or_spec:
            Model class (e.g. dataclass, Pydantic)
            or parsed ModelSpec/ResolvedModel.

        valid:
            If True, generate valid instances.
            If False, generate invalid ones.

        seed:
            Random seed for reproducible generation.
            - `None` (default): Use system randomness (different output each run).
            - `int`: Initialize RNG with fixed seed (same output for same seed).

        strategy:
            Define how fields are selected for violation when valid=False.

            - "first":
                take the first N constrained fields (default)

            - "random":
                take N random constrained fields

            - "all":
                generate one invalid case per constrained field (ignores count)

            - "all_violations":
                generate one invalid case per every available violations
                including constraints, structural and type violations (ignores count)

            - "field_name":
                violate a specific field using a dotted path
                (e.g. strategy="user.email")

            - "field_name::violation":
                violate a specific field with specific type
                (e.g. strategy="user.profile::below_min")

        count:
            Number of cases to generate (ignored if strategy="all").

        allow_type_mismatch:
            If True fields could be type mismatched.
            Available only when valid=False.

        allow_structural_violations:
            If True adding field missing to availiable field
            violations and cases with extra field in each model.
            Structural violations are available only when:
                - valid=False
                - strategy="all"

    Returns:
        A list of dictionaries.
    """
    if count < 1:
        raise api_error(
            "Count must be >= 1",
            code="invalid_count",
            count=count,
        )

    model = ensure_model_or_spec(model_or_spec)

    ctx = create_context(seed)

    if valid:
        if allow_type_mismatch:
            raise api_error(
                "Type mismatch is only available for invalid generation",
                code="invalid_flag_for_valid",
                flag="allow_type_mismatch",
            )

        if allow_structural_violations:
            raise api_error(
                "Structural violations are only available for invalid generation",
                code="invalid_flag_for_valid",
                flag="allow_structural_violations",
            )

        if strategy != "first":
            raise api_error(
                "Strategy selection is only applicable when valid=False",
                code="invalid_strategy_for_valid",
                strategy=strategy,
            )

        return [generate_valid(ctx, model) for _ in range(count)]

    field_strategy, forced_violation = parse_strategy_input(strategy)

    if (
        allow_structural_violations
        and field_strategy not in ("all", "all_violations")
        and forced_violation is None
    ):
        raise api_error(
            "Structural violations require strategy='all', 'all_violations', "
            "or explicit '::' syntax",
            code="invalid_strategy_for_structural",
            strategy=strategy,
        )

    if strategy == "all":
        tasks = plan_tasks(
            model,
            ctx=ctx,
            strategy="all",
            allow_all=True,
            allow_type_mismatch=allow_type_mismatch,
            allow_structural_violations=allow_structural_violations,
            split_by_violations=False,
        )

    elif strategy == "all_violations":
        tasks = plan_tasks(
            model,
            ctx=ctx,
            strategy="all",
            allow_all=True,
            allow_type_mismatch=allow_type_mismatch,
            allow_structural_violations=allow_structural_violations,
            split_by_violations=True,
        )

    else:
        tasks = plan_tasks(
            model,
            ctx=ctx,
            strategy=strategy,
            allow_all=False,
            count=count,
            allow_type_mismatch=allow_type_mismatch,
        )

    return [generate_invalid(ctx, model, task) for task in tasks]
