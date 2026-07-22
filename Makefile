.PHONY: help install dev-install test coverage lint format typecheck clean doctor

help:
	@echo "ShellSense AI - Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install       Install production dependencies"
	@echo "  make dev-install   Install development dependencies"
	@echo "  make test          Run tests"
	@echo "  make coverage      Run tests with coverage report"
	@echo "  make lint          Run ruff linter"
	@echo "  make format        Run black formatter"
	@echo "  make typecheck     Run mypy type checker"
	@echo "  make check         Run lint, typecheck, and test"
	@echo "  make clean         Remove build artifacts"
	@echo "  make doctor        Run system diagnostics"

install:
	pip install -r requirements.txt
	pip install -e .

dev-install:
	pip install -r requirements-dev.txt
	pip install -e .

test:
	python -m pytest tests/

coverage:
	python -m pytest --cov=shellsense --cov-report=term-missing --cov-report=html tests/

lint:
	python -m ruff check src/ tests/

format:
	python -m black src/ tests/

typecheck:
	python -m mypy src/

check: lint typecheck test

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/

doctor:
	python -m shellsense doctor
