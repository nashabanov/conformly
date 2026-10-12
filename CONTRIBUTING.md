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

Keep [README.md](README.md) focused on introduction and quickstart.
User guides live in [docs/](docs/README.md); executable public-API scenarios
live in [examples/](examples/README.md). Check claims against source and tests,
run affected examples, and verify relative links. Preserve precise contracts
for invalid generation, defaults, and diagnostic codes.

[Agent guide](AGENTS.md) · [Changelog](CHANGELOG.md) · [License](LICENSE)
