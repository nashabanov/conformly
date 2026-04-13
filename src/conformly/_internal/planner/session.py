from ._errors import planning_error

from conformly._internal.generator import GenerationContext
from conformly._internal.resolver import ResolvedModel
from conformly._internal.types import CasesStrategy, FieldPath

NameIndexMap = tuple[tuple[FieldPath, str], ...]


def select_paths(
    model: ResolvedModel,
    *,
    ctx: GenerationContext,
    strategy: CasesStrategy,
    allow_all: bool,
    count: int = 1,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
) -> tuple[FieldPath, ...]:
    candidates = _filter_candidate_paths(
        model=model,
        allow_type_mismatch=allow_type_mismatch,
        allow_structural_violations=allow_structural_violations,
    )

    if not candidates:
        raise planning_error(
            "No fields available for violation",
            code="no_violation_candidate",
            model=model.name,
            allow_type_mismatch=allow_type_mismatch,
            allow_structural_violations=allow_structural_violations,
        )

    return _select_violation_fields(
        ctx, strategy, allow_all, candidates, count, model.name_to_path
    )


def _filter_candidate_paths(
    model: ResolvedModel,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
) -> tuple[FieldPath, ...]:
    candidates = []

    for path, field in model.field_map.items():
        can_violate = (
            field.semantic.has_constraints
            or (allow_type_mismatch and field.nested_model is None)
            or allow_structural_violations
        )

        if can_violate:
            candidates.append(path)

    if allow_structural_violations:
        candidates.extend(model.extra_paths)

    return tuple(candidates)


def _select_violation_fields(
    ctx: GenerationContext,
    strategy: CasesStrategy,
    allow_all: bool,
    candidates: tuple[FieldPath, ...],
    count: int,
    name_to_path: dict[str, FieldPath],
) -> tuple[FieldPath, ...]:
    if strategy not in ("all", "random", "first"):
        if strategy not in name_to_path:
            raise planning_error(
                f"Field '{strategy}' not found",
                code="field_not_found",
                field=strategy,
                available=list(name_to_path.keys()),
            )

        path = name_to_path[strategy]
        if path not in candidates:
            raise planning_error(
                f"Field '{strategy} has no constraints'",
                code="no_constraints_field",
                field=strategy,
            )

        return (path,)

    if strategy == "all":
        if not allow_all:
            raise planning_error(
                "'all' strategy is only allowed in 'cases()', not 'case()'",
                code="all_strategy_not_allowed",
            )
        return candidates

    if strategy == "first":
        if count > len(candidates):
            raise planning_error(
                "Requested more fields than available",
                code="too_many_requested",
                requested=count,
                available=len(candidates),
            )
        return tuple(candidates[:count])

    if strategy == "random":
        if count > len(candidates):
            raise planning_error(
                "Requested more fields than available",
                code="too_many_requested",
                requested=count,
                available=len(candidates),
            )
        return tuple(ctx.rng.sample(candidates, k=count))

    raise planning_error(
        "Unhandled strategy", code="unhandled_strategy", strategy=strategy
    )
