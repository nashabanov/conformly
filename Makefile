.DEFAULT_GOAL := help

.PHONY: help \
        install install-dev install-all \
        sync sync-strict update lock clean \
        test test-all test-cov bench \
        lint lint-fix typecheck check \
        precommit


help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install        - Create venv and install dependencies"
	@echo "  make install-dev    - Install with dev dependencies"
	@echo "  make install-all    - Install with dev + all extras"
	@echo "  make sync           - Sync dependencies from lockfile"
	@echo "  make sync-strict    - Sync with frozen lockfile"
	@echo "  make update         - Upgrade dependencies"
	@echo "  make lock           - Update lockfile"
	@echo "  make clean          - Remove virtual environment"
	@echo ""
	@echo "Tests:"
	@echo "  make test           - Run unit tests (exclude benchmarks)"
	@echo "  make test-all       - Run all tests including benchmarks"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make bench          - Run only benchmarks"
	@echo ""
	@echo "Quality:"
	@echo "  make lint           - Run ruff linter"
	@echo "  make lint-fix       - Auto-fix lint issues"
	@echo "  make typecheck      - Run mypy type checker"
	@echo "  make check          - Run all checks"
	@echo "  make precommit      - Run pre-commit on all files"


.venv/bin/python:
	uv venv


install: .venv/bin/python
	uv sync
	uv pip install -e .


install-dev: .venv/bin/python
	uv sync --group dev
	uv pip install -e .


install-all: .venv/bin/python
	uv sync --group dev --all-extras
	uv pip install -e .


sync:
	uv sync
	uv pip install -e .

sync-strict:
	uv sync --frozen --group dev --all-extras
	uv pip install -e .


update:
	uv lock --upgrade
	uv sync --group dev


lock:
	uv lock


clean:
	rm -rf .venv


test:
	uv run -m pytest -m "not benchmark"


test-all:
	uv run -m pytest


test-cov:
	uv run -m pytest -m "not benchmark" \
		--cov=conformly \
		--cov-report=term-missing \
		--cov-fail-under=90


bench:
	uv run -m pytest -m benchmark --benchmark-only


lint:
	uv run -m ruff check .


lint-fix:
	uv run -m ruff check . --fix


typecheck:
	uv run -m mypy src/


check: lint typecheck test
	@echo "\033[0;32mAll checks passed!\033[0m"


precommit:
	uv run pre-commit run --all-files
