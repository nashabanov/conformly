from collections.abc import Callable
from typing import Any, NoReturn

from ._errors import api_error


class ProxyPath:
    __slots__ = ("_path",)

    _path: list[str]

    def __init__(self, path: list[str] | None = None) -> None:
        self._path = path or []

    def __getattr__(self, name: str) -> "ProxyPath":
        return ProxyPath([*self._path, name])

    def __getitem__(self, _: Any) -> NoReturn:
        raise api_error(
            "Indexing is not supported in path expressions. "
            "Use direct attribute access: x.field.subfield",
            code="path_unsupported_syntax",
            syntax_type="Subscript",
        )

    def __call__(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise api_error(
            "Method calls are not supported in path expressions.",
            code="path_unsupported_syntax",
            syntax_type="Call",
        )

    def _unwrap(self) -> list[str]:
        return self._path


def extract_path_from_proxy[T](expr: Callable[[T], Any]) -> str:
    proxy = ProxyPath()

    try:
        result = expr(proxy)  # type: ignore
    except TypeError as e:
        raise api_error(
            "Lambda must accept exactly one argument: lambda x: x.field",
            code="path_invalid_signature",
        ) from e

    if not isinstance(result, ProxyPath):
        raise api_error(
            "Lambda must return attribute access chain: lambda x: x.field.subfield",
            code="path_invalid_expression",
        )

    parts = result._unwrap()

    if not parts:
        raise api_error(
            "Empty path extracted from lambda",
            code="path_empty_result",
        )

    return ".".join(parts)
