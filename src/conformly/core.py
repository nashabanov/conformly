from random import sample
from typing import Any, Literal

from .generator import generate_invalid, generate_valid
from .parsing import parse_model
from .specs import ModelSpec
from .types import FieldPath

CaseStrategy = Literal["first", "random"] | str
CasesStrategy = Literal["first", "random", "all"] | str


def _ensure_model_or_spec(model_or_spec: ModelSpec | type) -> ModelSpec:
    if isinstance(model_or_spec, type):
        return parse_model(model_or_spec)
    return model_or_spec


def _gather_constrained_paths(spec: ModelSpec) -> list[tuple[FieldPath, str]]:
    result: list[tuple[FieldPath, str]] = []

    def dfs(current: ModelSpec, prefix: FieldPath, names: list[str]) -> None:
        for i, field in enumerate(current.fields):
            path = (*prefix, i)
            dotted = ".".join([*names, field.name])

            if field.constraints:
                result.append((path, dotted))

            if field.nested_model is not None:
                dfs(field.nested_model, path, [*names, field.name])

    dfs(spec, (), [])
    return result


def _select_violation_fields(
    spec: ModelSpec,
    *,
    strategy: CasesStrategy,
    allow_all: bool,
    count: int = 1,
) -> list[FieldPath]:
    constrained_fields = _gather_constrained_paths(spec)
    if not constrained_fields:
        raise ValueError("Cannot generate invalid case(s): no fields have constraints")

    name_to_path = {name: path for path, name in constrained_fields}
    all_paths = [path for path, _ in constrained_fields]

    if strategy not in ("all", "random", "first"):
        if strategy not in name_to_path:
            raise ValueError(
                f"Field '{strategy}' not found or has no constraints. "
                f"Available constrained fields: {list(name_to_path.keys())}"
            )
        return [name_to_path[strategy]]

    if strategy == "all":
        if not allow_all:
            raise ValueError(
                "'all' strategy is only allowed in 'cases()', not 'case()'"
            )
        return [path for path, _ in constrained_fields]

    if strategy == "first":
        if count > len(all_paths):
            raise ValueError(
                f"Requested {count} cases, but only "
                f"{len(all_paths)} constrained fields available"
            )
        return all_paths[:count]

    if strategy == "random":
        if count > len(all_paths):
            raise ValueError(
                f"Cannot select {count} random fields from "
                f"{len(all_paths)} constrained fields"
            )
        return sample(all_paths, k=count)

    raise AssertionError(f"Unhandled strategy: {strategy!r}")


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
    spec = _ensure_model_or_spec(model_or_spec)

    if valid:
        if strategy != "first":
            raise ValueError("Strategy is only applicable when valid=False")
        return generate_valid(spec)

    if strategy == "all":
        raise ValueError(
            "'all' strategy is not supported in 'case()' — use 'cases()' instead"
        )

    paths = _select_violation_fields(spec, strategy=strategy, allow_all=False, count=1)
    return generate_invalid(spec, paths[0])


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

    spec = _ensure_model_or_spec(model_or_spec)

    if valid:
        if strategy != "first":
            raise ValueError("Strategy is only applicable when valid=False")
        return [generate_valid(spec) for _ in range(count)]

    if strategy == "all":
        paths = _select_violation_fields(spec, strategy="all", allow_all=True)
        return [generate_invalid(spec, p) for p in paths]

    if isinstance(strategy, str) and strategy not in ("first", "random"):
        paths = _select_violation_fields(
            spec, strategy=strategy, allow_all=False, count=1
        )
        return [generate_invalid(spec, paths[0])]

    paths = _select_violation_fields(
        spec, strategy=strategy, allow_all=False, count=count
    )
    return [generate_invalid(spec, p) for p in paths]
