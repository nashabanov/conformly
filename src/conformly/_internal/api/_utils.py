from typing import Any

from .path import PathSelector, parse_strategy_input

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


def plan_tasks(
    model: ResolvedModel,
    *,
    ctx: GenerationContext,
    strategy: CasesStrategy | PathSelector,
    allow_all: bool,
    count: int | None = None,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
    split_by_violations: bool = False,
) -> list[PlannedTask]:
    field_strategy, forces_violations = parse_strategy_input(strategy)

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
