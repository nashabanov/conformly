from typing import Any

from conformly.exceptions import GenerationError


def api_error(message: str, *, code: str, **context: Any) -> GenerationError:
    return GenerationError(message, context={"code": code, **context})
