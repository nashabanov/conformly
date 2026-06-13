import ast
from collections.abc import Callable
import contextlib
from dataclasses import dataclass
import inspect
import textwrap
from typing import Any, overload
import weakref

from ._errors import api_error

from conformly._internal.types import ViolationType


@dataclass(frozen=True, slots=True)
class PathSelector:
    raw_path: str
    forced_violation: ViolationType | None = None

    def violate(self, violation: ViolationType) -> "PathSelector":
        return PathSelector(self.raw_path, violation)


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
            DSL object that can be refined with `.violate(ViolationType)`.

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

    raw_path = _extract_path_from_lambda(expr)
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


_path_cache: weakref.WeakKeyDictionary[Callable[[Any], Any], str] = (
    weakref.WeakKeyDictionary()
)


def _extract_path_from_lambda(expr: Callable[[Any], Any]) -> str:
    if expr in _path_cache:
        return _path_cache[expr]

    try:
        source = inspect.getsource(expr)
    except (OSError, TypeError) as e:
        raise api_error(
            "path(Model, lambda) requires source code availability (.py file). "
            "In REPL/Jupyter, use string mode: path('field.nested').",
            code="path_source_unavailable",
        ) from e

    source = textwrap.dedent(source)

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise api_error(
            f"Failed to parse lambda expression: {e}",
            code="path_syntax_error",
        ) from e

    lambda_node = _find_lambda(tree)
    if lambda_node is None:
        raise api_error(
            "Lambda not found in source. Pass the function directly: "
            "path(Model, lambda x: x.field)",
            code="path_lambda_not_found",
        )

    if not lambda_node.args.args:
        raise api_error(
            f"Lambda must accept exactly one argument, but got "
            f"{len(lambda_node.args.args)}.",
            code="path_invalid_signature",
        )

    param_name = lambda_node.args.args[0].arg
    parts = _collect_path_parts(lambda_node.body, param_name)

    if not parts:
        raise api_error(
            f"Could not extract path from expression. "
            f"Expected format: lambda {param_name}: {param_name}.field.subfield",
            code="path_empty_result",
        )

    path_str = ".".join(parts)

    with contextlib.suppress(TypeError):
        _path_cache[expr] = path_str

    return path_str


def _find_lambda(tree: ast.AST) -> ast.Lambda | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            return node
    return None


def _collect_path_parts(node: ast.AST, param_name: str) -> list[str]:
    parts: list[str] = []
    current = node

    while True:
        if isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        elif isinstance(current, ast.Call):
            raise api_error(
                "Method calls (e.g., u.get_name()) are not supported. "
                "Only direct field access (e.g., u.field) is allowed.",
                code="path_unsupported_syntax",
                syntax_type="Call",
            )

        elif isinstance(current, ast.Name):
            if current.id != param_name:
                raise api_error(
                    f"Expression must start with lambda parameter '{param_name}', "
                    f"but found '{current.id}'.",
                    code="path_invalid_root",
                    expected_param=param_name,
                    found_param=current.id,
                )
            break

        else:
            if not parts:
                raise api_error(
                    f"Unsupported expression type: {type(current).__name__}. "
                    f"Expected attribute chain: lambda x: x.field.subfield",
                    code="path_unsupported_syntax",
                    syntax_type=type(current).__name__,
                )
            break

    parts.reverse()
    return parts
