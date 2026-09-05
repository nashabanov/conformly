# Agent Guide

## Repository Scope

- Conformly generates valid fixtures and minimal invalid cases from typed Python models.
- Core models are dataclasses and TypedDicts; Pydantic and attrs support is optional.
- Public behavior belongs in the API and adapter layers; `_internal/` modules are implementation details.

## Project Layout

- This is a single Python package using the `src/` layout; implementation is under `src/conformly/`, tests under `tests/`.
- The public API is exposed from `conformly`: `case`, `cases`, `path`, constraints, special field types, and `V`; use these entrypoints instead of importing `_internal` modules.
- API orchestration lives under `src/conformly/_internal/api/`; most other implementation details live under `src/conformly/_internal/`.
- Built-in dataclass and TypedDict adapters are always registered; Pydantic and attrs adapters register automatically only when their optional dependencies are installed.

## Architecture

- The generation pipeline is `case/cases/path` -> adapter parser -> immutable `ModelSpec` -> resolver/semantics -> planner -> type generators.
- Adapters translate framework-specific models into the shared `ModelSpec`; keep framework-specific behavior in adapters rather than API, resolver, or generators.
- The resolver validates constraints and produces semantic models; the planner selects target paths and violations; generators only produce values from resolved semantics.
- Prefer functional transformations and small stateless functions over stateful service objects. Keep intermediate specs, semantics, paths, and violation collections immutable; use tuples and frozen models where practical.
- Avoid creating wrapper objects or copying model state without a concrete need. Reuse resolved models and cached parser results, and keep mutable state limited to generation context, RNG, and explicitly requested tracing.
- Invalid generation should target one selected path while generating valid values for the rest; do not bypass planning to mutate arbitrary fields.

## Dependencies And Supported Models

- Core runtime depends only on `rstr`; dataclasses and TypedDicts work without extras.
- Pydantic support requires `conformly[pydantic]` and attrs support requires `conformly[attrs]`; use `make install-all` for the complete adapter and integration test suite.
- Optional packages must remain lazily imported. Importing `conformly` must not require Pydantic or attrs; missing adapters should fail only when their model is used.
- Pydantic constraints are extracted from `Field` metadata; `constr`, `conint`, and functional validators are not interpreted.
- Nested models are supported, but cyclic references and nested collections such as `list[list[T]]` are not.
- Dictionary keys are limited to `str` and Enum/Literal-compatible types.

## Tests

- Keep tests in the layer they exercise: parsing, resolver, planner, generators, API/path, or integration under the corresponding `tests/` subdirectory.
- Pydantic integration tests use `pytest.importorskip`; without the optional dependency they are skipped, not expected to pass through the adapter.
- Add integration coverage when changing cross-layer behavior, and mark performance tests with pytest's `benchmark` marker.

## Environment And Commands

- Use Python `>=3.12` and `uv`; `make install-dev` installs development dependencies, while `make install-all` also installs Pydantic and attrs extras.
- Use `make sync-strict` when reproducing CI-style dependencies; it uses the locked `uv.lock` file and all extras.
- `make test` runs non-benchmark tests. Use `uv run -m pytest tests/path/to/test.py::test_name` for a focused test.
- `make test-all` includes benchmark-marked tests; `make bench` runs only benchmarks. `make test-cov` requires at least 90% coverage.
- `make check` runs `lint`, then `typecheck`, then non-benchmark `test`; run it before declaring a change verified.
- `make lint-fix` modifies files; inspect its diff before keeping the fixes. `make precommit` runs all configured hooks on all files.

## Tooling Constraints

- Ruff targets Python 3.13 with an 88-character line length; mypy is strict and checks `src/` with Python 3.13 settings, even though the package supports Python 3.12+.
- Keep benchmark tests marked with pytest's `benchmark` marker; the default test command excludes them.
- Update `uv.lock` through `make lock` or `make update` when dependency declarations change; do not hand-edit the lockfile.
