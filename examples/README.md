# Executable examples

Run from a checkout with Python 3.12+ and `uv`:

```bash
uv run examples/basic_generation.py
uv run examples/invalid_generation.py
uv run examples/nested_models.py
uv run examples/pytest_integration.py
uv run --extra pydantic examples/pydantic_integration.py
uv run --extra attrs examples/attrs_integration.py
uv run -m pytest examples/pytest_integration.py
```

Each script is independent and uses only the public API. In an installed
Python environment, use `python examples/<filename>.py` after installing its
listed dependencies. Random values are printed for inspection; assertions
check behavior without depending on particular generated values.

| Example | Purpose | Dependencies |
| --- | --- | --- |
| [basic_generation.py](basic_generation.py) | Valid constrained dataclass payload and batch | Core |
| [invalid_generation.py](invalid_generation.py) | Field targeting, explicit violation, field enumeration | Core |
| [nested_models.py](nested_models.py) | Models in collections and one nested invalid target | Core |
| [pytest_integration.py](pytest_integration.py) | Positive and negative application validation tests | Core; pytest for runner |
| [pydantic_integration.py](pydantic_integration.py) | `Field` extraction and Pydantic validation | `conformly[pydantic]` |
| [attrs_integration.py](attrs_integration.py) | `Annotated` constraints and model defaults | `conformly[attrs]` |

[Getting started](../docs/getting-started.md) · [Documentation](../docs/README.md)
