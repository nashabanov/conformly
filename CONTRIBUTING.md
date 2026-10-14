# Contributing

Contributions welcome. Fork the repository, create a feature branch, add tests
for behavior changes, and submit a pull request. Use Python 3.12 or newer and `uv`.

## Setup and checks

```bash
make install-dev     # Development dependencies
make install-all     # Development dependencies and all optional integrations
make sync-strict     # Frozen lockfile, development group, all extras
make check           # Ruff, strict mypy, non-benchmark tests
```

Other useful commands:

- `make test`: non-benchmark tests.
- `make test-all`: tests including benchmarks.
- `make test-cov`: coverage check with a 90% minimum.
- `make bench`: benchmarks only.
- `make lint`, `make typecheck`: individual quality checks.
- `make lint-fix`: apply lint fixes; inspect the diff.
- `make precommit`: all configured hooks.
- `make lock`, `make update`: update dependencies and the lockfile.

## Documentation maintenance

Documentation is written in English and maintained alongside behavior changes.
Describe supported behavior confirmed by source and tests; state limitations
explicitly rather than implying support from an annotation or adapter alone.

### Where information belongs

- [README.md](README.md): package purpose, installation, capabilities, and a short
  quickstart. Link to detailed guides instead of duplicating them. It is also the
  PyPI description, so use absolute GitHub links for repository files and anchors.
- [docs/README.md](docs/README.md): navigation to user guides. Add or update its
  links when pages are added, renamed, or reorganized.
- [Getting started](docs/getting-started.md): installation and first validation
  tests. [Generation](docs/generation.md): payload shapes, supported types,
  defaults, and limitations. [Constraints](docs/constraints.md): declarations,
  compatibility, and boundaries.
- [Strategies](docs/strategies.md): automatic selection, explicit targets,
  violations, and the invalid generation contract.
  [Integrations](docs/integrations.md): adapter behavior and optional dependencies.
  [Advanced usage](docs/advanced.md): overrides, diagnostics, and tracing.
- [API reference](docs/api-reference.md): public exports, signatures, defaults,
  accepted parameter combinations, and errors. Keep these aligned with the public
  API; explain implementation architecture in the agent guide rather than here.
- [examples/](examples/README.md): independent, executable public-API scenarios.
  Keep the example index, dependency requirements, and run commands up to date.
- [CHANGELOG.md](CHANGELOG.md): user-visible changes under the appropriate release
  and Added/Changed/Fixed sections. Mark breaking changes and show how to migrate.
  Preserve historical entries; align the release version with `pyproject.toml`
  and regenerate `uv.lock` through `make lock` when changing the package version.

Use relative links within `docs/`, `examples/`, and contributor documentation.
Prefer linking to the page that owns a contract over repeating its full details.

### Contracts and examples

- Use public imports from `conformly` and documented public submodules such as
  `conformly.exceptions` and `conformly.tracer`; do not teach `_internal` imports.
- Keep snippets runnable on Python 3.12+. Include imports and model definitions,
  or explicitly identify a preceding example they depend on.
- Separate core examples from optional integrations. List required extras and use
  the extra-specific `uv run` commands shown in the example index.
- Assert constraints and payload behavior instead of particular random values.
  Use a fixed seed when demonstrating reproducibility, and explain that user
  default factories are outside the seeded RNG.
- Preserve precise guarantees: results are dictionaries; invalid generation
  plans one target and guarantees the selected violation, while defaults and
  supplied override values are trusted. Explain target/strategy/count rules,
  override precedence, and collection routing wherever affected by a change.
- Distinguish adapter-specific validation from shared generation behavior. Keep
  unsupported model shapes, constraint extraction limits, and experimental
  features visible in the relevant guide.
- For errors, use the actual exception class and diagnostic `context` keys/codes.
  Do not promise identical context fields for every error or wrap arbitrary
  third-party exceptions in a documented guarantee.

### Verification

For each documentation change, inspect the diff and verify local link targets
and heading anchors. For behavior changes, update the affected guide, API
reference, examples, and changelog together as applicable; remove obsolete syntax
from current documentation while retaining it in migration examples and history.
Run modified executable examples with their declared dependencies, including
`uv run -m pytest examples/pytest_integration.py` when that scenario changes.
Exercise changed Python snippets or verify them against matching public-API
tests. Run `make check` for code changes; prose-only edits need link and content
verification, not a new test suite.

[Agent guide](AGENTS.md) · [Changelog](CHANGELOG.md) · [License](LICENSE)
