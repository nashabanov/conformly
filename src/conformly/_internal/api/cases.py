from typing import Any

from ._errors import api_error
from ._utils import (
    ensure_model_or_spec,
    normalize_overrides,
    plan_tasks,
    validate_selection,
)
from .path import PathSelector

from conformly._internal.generator.context import create_context
from conformly._internal.generator.orchestration import generate_invalid, generate_valid
from conformly._internal.parser.models import ModelSpec
from conformly._internal.types.strategies import CasesStrategy


def cases(
    model_or_spec: ModelSpec | type,
    *,
    valid: bool = True,
    seed: int | None = None,
    strategy: CasesStrategy = "first",
    target: PathSelector | None = None,
    count: int = 1,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
    overrides: list[PathSelector] | None = None,
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
            Random seed for reproducible internal generation.
            - `None` (default): Use system randomness (different output each run).
            - `int`: Initialize RNG with a fixed seed, including 0 and negatives.
            User-provided default factories must be deterministic for identical
            payloads; their randomness is not controlled by this seed.

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

        target:
            Optional selector from path("field") or path(Model, lambda m: m.field).
            Only available with valid=False and strategy="first".
            Use .violate(V.X) to request an exact violation.

        count:
            Number of cases; target requires 1. Enumeration ignores count.

        overrides:
            Optional list of `PathSelector` to set field values.
            - Used instead of generated values and model defaults
            - With valid=False: act as defaults (ignored if field is violated)


        allow_type_mismatch:
            If True fields could be type mismatched.
            Available only when valid=False.

        allow_structural_violations:
            If True adding field missing to availiable field
            violations and cases with extra field in each model.
            Structural violations are available only when:
                - valid=False
                - strategy="all" or "all_violations", or an explicit violation

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

    _overrides = normalize_overrides(model, overrides)

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

    validate_selection(
        valid=valid,
        strategy=strategy,
        target=target,
        allow_all=True,
        count=count,
    )

    if valid:
        return [generate_valid(ctx, model, _overrides) for _ in range(count)]

    if (
        allow_structural_violations
        and strategy not in ("all", "all_violations")
        and (target is None or target.forced_violation is None)
    ):
        raise api_error(
            "Structural violations require strategy='all', 'all_violations', "
            "or an explicit violation on target",
            code="invalid_strategy_for_structural",
            strategy=strategy,
        )

    tasks = plan_tasks(
        model,
        ctx=ctx,
        strategy="all" if strategy == "all_violations" else strategy,
        target=target,
        allow_all=True,
        count=count,
        allow_type_mismatch=allow_type_mismatch,
        allow_structural_violations=allow_structural_violations,
        split_by_violations=strategy == "all_violations",
    )

    return [generate_invalid(ctx, model, task, _overrides) for task in tasks]
