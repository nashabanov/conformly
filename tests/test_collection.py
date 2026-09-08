"""Keep test functions visible to pytest collection."""

import ast
from pathlib import Path


def test_no_test_functions_are_nested_inside_functions() -> None:
    tests_root = Path(__file__).parent
    hidden = set()
    function_nodes = (ast.FunctionDef, ast.AsyncFunctionDef)

    for source in tests_root.rglob("test_*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for outer in ast.walk(tree):
            if not isinstance(outer, function_nodes):
                continue
            for inner in ast.walk(outer):
                if (
                    inner is not outer
                    and isinstance(inner, function_nodes)
                    and inner.name.startswith("test_")
                ):
                    hidden.add(
                        f"{source.relative_to(tests_root)}:{inner.lineno}: {inner.name}"
                    )

    assert not hidden, "Tests hidden from pytest collection:\n" + "\n".join(
        sorted(hidden)
    )
