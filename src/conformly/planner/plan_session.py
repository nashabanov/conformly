import random

from ..resolver import ResolvedModel
from ..types import CasesStrategy, FieldPath

NameIndexMap = tuple[tuple[FieldPath, str], ...]


def select_paths(
    model: ResolvedModel,
    *,
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
        raise ValueError("Cannot generate invalid case(s): no fields have constraints")

    return _select_violation_fields(
        strategy, allow_all, candidates, count, model.name_to_path
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
    strategy: CasesStrategy,
    allow_all: bool,
    candidates: tuple[FieldPath, ...],
    count: int,
    name_to_path: dict[str, FieldPath],
) -> tuple[FieldPath, ...]:
    if strategy not in ("all", "random", "first"):
        if strategy not in name_to_path:
            raise ValueError(
                f"Field '{strategy}' not found or has no constraints. "
                f"Available constrained fields: {list(name_to_path.keys())}"
            )

        path = name_to_path[strategy]
        if path not in candidates:
            raise ValueError(f"Field '{strategy}' has no constraints to violate")

        return (path,)

    if strategy == "all":
        if not allow_all:
            raise ValueError(
                "'all' strategy is only allowed in 'cases()', not 'case()'"
            )
        return candidates

    if strategy == "first":
        if count > len(candidates):
            raise ValueError(
                f"Requested {count} cases, but only "
                f"{len(candidates)} constrained fields available"
            )
        return tuple(candidates[:count])

    if strategy == "random":
        if count > len(candidates):
            raise ValueError(
                f"Cannot select {count} random fields from "
                f"{len(candidates)} constrained fields"
            )
        return tuple(random.sample(candidates, k=count))

    raise AssertionError(f"Unhandled strategy: {strategy!r}")
