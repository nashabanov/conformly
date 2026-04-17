from dataclasses import dataclass

from ._errors import api_error

from conformly._internal.types import ViolationType


@dataclass(frozen=True, slots=True)
class PathSelector:
    raw_path: str
    forced_violation: ViolationType | None = None

    def violate(self, violation: ViolationType) -> "PathSelector":
        return PathSelector(self.raw_path, violation)


def path(raw: str) -> PathSelector:
    """
    Create a field path selector for violation targeting.

    Supported usage:
        path("user.email").violate(V.TOO_SHORT)
        path("bio").violate(V.TOO_LONG)

    Args:
        raw:
            Dotted path to a field inside the model.
            Example: "user.email", "profile.address.street"

    Returns:
        PathSelector:
            DSL object that can be refined with:
                - .violate(ViolationType)

    Notes:
        This API does not validate the path immediately.
        Validation is performed during planning stage
        against the resolved model structure.
    """
    return PathSelector(raw)


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
