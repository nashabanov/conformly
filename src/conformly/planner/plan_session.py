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
    constrained_fields = _gather_constrained_paths(
        model, allow_type_mismatch, allow_structural_violations
    )

    if not constrained_fields:
        raise ValueError("Cannot generate invalid case(s): no fields have constraints")

    return _select_violation_fields(strategy, allow_all, constrained_fields, count)


def _gather_constrained_paths(
    model: ResolvedModel,
    allow_type_mismatch: bool = False,
    allow_structural_violations: bool = False,
) -> NameIndexMap:
    result: list[tuple[FieldPath, str]] = []

    def dfs(current: ResolvedModel, prefix: FieldPath, names: list[str]) -> None:
        for i, field in enumerate(current.fields):
            path = (*prefix, i)
            dotted = ".".join([*names, field.name])

            can_violate = (
                field.semantic.has_constraints
                or (allow_type_mismatch and field.nested_model is None)
                or allow_structural_violations
            )

            if can_violate:
                result.append((path, dotted))

            if field.nested_model is not None:
                dfs(field.nested_model, path, [*names, field.name])

        if allow_structural_violations:
            extra_index = len(current.fields)
            extra_path = (*prefix, extra_index)
            extra_dotted = (".".join(names) + ":extra") if names else ":extra"
            result.append((extra_path, extra_dotted))

    dfs(model, (), [])
    return tuple(result)


def _select_violation_fields(
    strategy: CasesStrategy,
    allow_all: bool,
    constrained_fields: NameIndexMap,
    count: int,
) -> tuple[FieldPath, ...]:
    name_to_path = {name: path for path, name in constrained_fields}
    all_paths = [path for path, _ in constrained_fields]

    if strategy not in ("all", "random", "first"):
        if strategy not in name_to_path:
            raise ValueError(
                f"Field '{strategy}' not found or has no constraints. "
                f"Available constrained fields: {list(name_to_path.keys())}"
            )
        return (name_to_path[strategy],)

    if strategy == "all":
        if not allow_all:
            raise ValueError(
                "'all' strategy is only allowed in 'cases()', not 'case()'"
            )
        return tuple(path for path, _ in constrained_fields)

    if strategy == "first":
        if count > len(all_paths):
            raise ValueError(
                f"Requested {count} cases, but only "
                f"{len(all_paths)} constrained fields available"
            )
        return tuple(all_paths[:count])

    if strategy == "random":
        if count > len(all_paths):
            raise ValueError(
                f"Cannot select {count} random fields from "
                f"{len(all_paths)} constrained fields"
            )
        return tuple(random.sample(all_paths, k=count))

    raise AssertionError(f"Unhandled strategy: {strategy!r}")
