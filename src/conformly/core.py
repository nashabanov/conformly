from typing import Any

from ._internal.parser import ModelSpec, parse_model
from ._internal.planner import PlannedTask, plan_violation_task, select_paths
from ._internal.types import CasesStrategy, CaseStrategy, ViolationType
from .generator import (
    GenerationContext,
    create_context,
    generate_invalid,
    generate_valid,
)
from .resolver import ResolvedModel, resolve_model


def _ensure_model_or_spec(
    model_or_spec: ModelSpec | ResolvedModel | type,
) -> ResolvedModel:
    if isinstance(model_or_spec, ResolvedModel):
        return model_or_spec

    if isinstance(model_or_spec, ModelSpec):
        return resolve_model(model_or_spec)

    return resolve_model(parse_model(model_or_spec))


def _parse_strategy_input(strategy: str) -> tuple[str, ViolationType | None]:
    if "::" in strategy:
        field_part, violation_part = strategy.split("::", 1)
        try:
            v_type = ViolationType(violation_part)
            return field_part, v_type
        except ValueError:
            available = [v.value for v in ViolationType]
            raise ValueError(
                f"Unknown violation type '{violation_part}'. "
                f"Available types: {', '.join(available)}"
            )
    return strategy, None


def _plan_tasks(
    model: ResolvedModel,
    *,
    ctx: GenerationContext,
    strategy: CasesStrategy,
    allow_all: bool,
    count: int | None = None,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
    split_by_violations: bool = False,
) -> list[PlannedTask]:
    field_strategy, forces_violations = _parse_strategy_input(strategy)

    paths = select_paths(
        model,
        ctx=ctx,
        strategy=field_strategy,
        allow_all=allow_all,
        count=count or 1,
        allow_type_mismatch=allow_type_mismatch,
        allow_structural_violations=allow_structural_violations,
    )

    if split_by_violations:
        return [
            PlannedTask(path=path, allowed_violations=(violation,))
            for path in paths
            for violation in plan_violation_task(
                model, path, allow_type_mismatch, allow_structural_violations
            ).allowed_violations
        ]

    return [
        plan_violation_task(
            model=model,
            path=path,
            allow_type_mismatch=allow_type_mismatch,
            allow_structural_violations=allow_structural_violations,
            forced_violation=forces_violations,
        )
        for path in paths
    ]


# ===== case =====
def case(
    model_or_spec: ModelSpec | type,
    *,
    valid: bool = True,
    seed: int | None = None,
    strategy: CaseStrategy = "first",
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

        allow_type_mismatch:
            If True fields could be type mismatched.
            Availiable only when valid=False.

    Returns:
        A dictionary representing the instance.
    """
    model = _ensure_model_or_spec(model_or_spec)

    ctx = create_context(seed)

    if valid:
        if allow_type_mismatch:
            raise ValueError("Type mismatching availiable inly for invald generation")

        if strategy != "first":
            raise ValueError("Strategy is only applicable when valid=False")
        return generate_valid(ctx, model)

    if strategy == "all":
        raise ValueError(
            "'all' strategy is not supported in 'case()' — use 'cases()' instead"
        )

    task = _plan_tasks(
        model,
        ctx=ctx,
        strategy=strategy,
        allow_all=False,
        count=1,
        allow_type_mismatch=allow_type_mismatch,
    )[0]
    return generate_invalid(ctx, model, task)


# ===== cases =====
def cases(
    model_or_spec: ModelSpec | type,
    *,
    valid: bool = True,
    seed: int | None = None,
    strategy: CasesStrategy = "first",
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
        raise ValueError("count must be >= 1")

    model = _ensure_model_or_spec(model_or_spec)

    ctx = create_context(seed)

    if valid:
        if allow_type_mismatch:
            raise ValueError("Type mismatching availiable only for invalid generation")

        if allow_structural_violations:
            raise ValueError(
                "Structural violations availiable only for invalid generation"
            )

        if strategy != "first":
            raise ValueError("Strategy is only applicable when valid=False")

        return [generate_valid(ctx, model) for _ in range(count)]

    if (
        allow_structural_violations
        and strategy not in ("all", "all_violations")
        and "::" not in strategy
    ):
        raise ValueError(
            "Structural violations (MISSING_FIELD, EXTRA_FIELD) are only supported "
            f"with strategy='all'|'all_violations' or explicit '::' syntax, "
            f"got strategy='{strategy}'"
        )

    if strategy == "all":
        tasks = _plan_tasks(
            model,
            ctx=ctx,
            strategy="all",
            allow_all=True,
            allow_type_mismatch=allow_type_mismatch,
            allow_structural_violations=allow_structural_violations,
            split_by_violations=False,
        )

    elif strategy == "all_violations":
        tasks = _plan_tasks(
            model,
            ctx=ctx,
            strategy="all",
            allow_all=True,
            allow_type_mismatch=allow_type_mismatch,
            allow_structural_violations=allow_structural_violations,
            split_by_violations=True,
        )

    else:
        tasks = _plan_tasks(
            model,
            ctx=ctx,
            strategy=strategy,
            allow_all=False,
            count=count,
            allow_type_mismatch=allow_type_mismatch,
        )

    return [generate_invalid(ctx, model, task) for task in tasks]
