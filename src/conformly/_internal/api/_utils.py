from typing import Any

from ._errors import api_error
from .path import PathSelector

from conformly._internal.generator import GenerationContext
from conformly._internal.parser import ModelSpec, parse_model
from conformly._internal.planner import PlannedTask, plan_violation_task, select_paths
from conformly._internal.resolver import ResolvedModel, resolve_model
from conformly._internal.types import CasesStrategy, FieldPath


def ensure_model_or_spec(
    model_or_spec: ModelSpec | ResolvedModel | type,
) -> ResolvedModel:
    if isinstance(model_or_spec, ResolvedModel):
        return model_or_spec

    if isinstance(model_or_spec, ModelSpec):
        return resolve_model(model_or_spec)

    return resolve_model(parse_model(model_or_spec))


def normalize_overrides(
    model: ResolvedModel, overrides: list[PathSelector] | None
) -> dict[FieldPath, Any] | None:
    if overrides is None:
        return None

    normalized_overrides: dict[FieldPath, Any] = {}

    for v in overrides:
        path = model.name_to_path.get(v.raw_path)
        if path:
            normalized_overrides[path] = v.override

    return normalized_overrides


def validate_selection(
    *,
    valid: bool,
    strategy: CasesStrategy,
    target: PathSelector | None,
    allow_all: bool,
    count: int = 1,
) -> None:
    if valid and strategy != "first":
        raise api_error(
            "Strategy selection is only applicable when valid=False",
            code="invalid_strategy_for_valid",
            strategy=strategy,
        )
    supported = (
        ("first", "random", "all", "all_violations")
        if allow_all
        else ("first", "random")
    )
    if not isinstance(strategy, str) or strategy not in supported:
        raise api_error(
            "Unsupported strategy",
            code="unsupported_strategy",
            function="cases" if allow_all else "case",
            strategy=strategy,
            available=list(supported),
        )
    if target is not None:
        if not isinstance(target, PathSelector):
            raise api_error(
                "Target must be a PathSelector; use path('field')",
                code="invalid_target",
            )
        if valid:
            raise api_error(
                "Target selection is only applicable when valid=False",
                code="invalid_target_for_valid",
                target=target.raw_path,
            )
        if strategy != "first":
            raise api_error(
                "Explicit targets require strategy='first'",
                code="invalid_strategy_for_target",
                strategy=strategy,
                target=target.raw_path,
            )
        if count != 1:
            raise api_error(
                "Explicit targets require count=1",
                code="invalid_count_for_target",
                count=count,
                target=target.raw_path,
            )


def plan_tasks(
    model: ResolvedModel,
    *,
    ctx: GenerationContext,
    strategy: CasesStrategy,
    target: PathSelector | None = None,
    allow_all: bool,
    count: int = 1,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
    split_by_violations: bool = False,
) -> list[PlannedTask]:
    forced_violation = target.forced_violation if target is not None else None

    paths = select_paths(
        model,
        ctx=ctx,
        strategy=strategy,
        target=target.raw_path if target is not None else None,
        forced_violation=forced_violation,
        allow_all=allow_all,
        count=count,
        allow_type_mismatch=allow_type_mismatch,
        allow_structural_violations=allow_structural_violations,
    )

    if split_by_violations:
        return [
            plan_violation_task(
                model,
                path,
                allow_type_mismatch,
                allow_structural_violations,
                forced_violation=violation,
            )
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
            forced_violation=forced_violation,
        )
        for path in paths
    ]
