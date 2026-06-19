from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, overload

from ._errors import api_error
from ._path_proxy import extract_path_from_proxy

from conformly._internal.types import ViolationType


@dataclass(frozen=True, slots=True)
class PathSelector:
    raw_path: str
    forced_violation: ViolationType | None = None
    override: Any | None = None

    def set(self, override: Any) -> "PathSelector":
        return PathSelector(self.raw_path, override=override)

    def violate(self, violation: ViolationType) -> "PathSelector":
        return PathSelector(self.raw_path, forced_violation=violation)


@overload
def path(target: str) -> PathSelector: ...


@overload
def path[T](target: type[T], expr: Callable[[T], Any]) -> PathSelector: ...


def path[T](
    target: str | type[T], expr: Callable[[T], Any] | None = None
) -> PathSelector:
    """
    Create a field path selector for violation targeting.

    Supports two usage modes:

    1. String mode (simple, backward-compatible):
        path("user.email").violate(V.TOO_SHORT)
        path("bio").violate(V.TOO_LONG)

    2. Typed lambda mode (IDE-friendly, type-safe):
        path(User, lambda u: u.profile.email).violate(V.TOO_SHORT)
        path(User, lambda u: u.age).violate(V.TOO_LOW)

    Args:
        target:
            Either a dotted path string, or a model class for typed resolution.
        expr:
            Lambda expression targeting a field. Required when `raw_or_model`
            is a class. Example: `lambda u: u.profile.email`

    Returns:
        PathSelector:
            DSL object that can be refined with
            `.violate(ViolationType)` or `.set(Any)`.

    Notes:
        - String paths are not validated immediately. Validation occurs during
          the planning stage against the resolved model structure.
        - Lambda paths require source code availability (.py files). In REPL
          or Jupyter, use the string mode.
    """
    if isinstance(target, str):
        if expr is not None:
            raise api_error(
                "path(str) does not accept a lambda expression. "
                "Use path('field') or path(Model, lambda x: x.field).",
                code="invalid_path_argument",
            )
        return PathSelector(target)

    if expr is None:
        raise api_error(
            "path(Model) requires a lambda expression as the second argument. "
            "Usage: path(Model, lambda x: x.field)",
            code="invalid_path_argument",
        )

    raw_path = extract_path_from_proxy(expr)
    return PathSelector(raw_path)


def parse_strategy_input(
    strategy: str | PathSelector,
) -> tuple[str, ViolationType | None]:
    if isinstance(strategy, PathSelector):
        return strategy.raw_path, strategy.forced_violation

    if "::" in strategy:
        field_part, violation_part = strategy.split("::", 1)
        try:
            v_type = ViolationType(violation_part)
            return field_part, v_type
        except ValueError:
            available = [v.value for v in ViolationType]
            raise api_error(
                f"Unknown violation type '{violation_part}'",
                code="invalid_violation_type",
                requested=violation_part,
                available=available,
            )
    return strategy, None
