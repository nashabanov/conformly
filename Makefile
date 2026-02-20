.PHONY: help test test-all bench lint typecheck

help:
	@echo "Available commands:"
	@echo "  make test           - Run unit tests (exclude benchmarks)"
	@echo "  make test-all       - Run all tests including benchmarks"
	@echo "  make bench          - Run only benchmarks"
	@echo "  make lint           - Run ruff linter"
	@echo "  make typecheck      - Run mypy type checker"
	@echo "  make check          - Run all checks (lint + typecheck + test)"


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
