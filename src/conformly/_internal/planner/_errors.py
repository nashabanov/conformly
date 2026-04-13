from typing import Any

from conformly.exceptions import PlanningError


def planning_error(message: str, *, code: str, **context: Any) -> PlanningError:
    return PlanningError(
        message,
        context={
            "code": code,
            **context,
        },
    )
