# Makefile for 사주 project
# Enforces Python 3.12.11 via scripts/py helper

PYTHON := ./scripts/py
PYTEST := $(PYTHON) -m pytest
PYTHONPATH := .:services/analysis-service:services/common

.PHONY: help
help:
	@echo "사주 Project Makefile"
	@echo ""
	@echo "Test targets:"
	@echo "  make test                 - Run all tests"
	@echo "  make test-unit            - Run unit tests only"
	@echo "  make test-integration     - Run integration tests"
	@echo "  make test-luck-pillars    - Run Luck Pillars engine tests"
	@echo "  make test-ten-gods        - Run Ten Gods engine tests"
	@echo "  make test-twelve-stages   - Run Twelve Stages engine tests"
	@echo ""
	@echo "Code quality:"
	@echo "  make lint                 - Run linter (ruff)"
	@echo "  make format               - Format code (ruff)"
	@echo "  make typecheck            - Run type checker (mypy)"
	@echo ""
	@echo "Environment:"
	@echo "  make venv                 - Create/rebuild virtual environment"
	@echo "  make clean                - Remove venv and caches"
	@echo "  make verify-python        - Verify Python version"

.PHONY: test
test:
	PYTHONPATH=$(PYTHONPATH) $(PYTEST) services/analysis-service/tests/ -v

.PHONY: test-unit
test-unit:
	PYTHONPATH=$(PYTHONPATH) $(PYTEST) services/analysis-service/tests/test_*.py -v -k "not integration"

.PHONY: test-integration
test-integration:
	PYTHONPATH=$(PYTHONPATH) $(PYTEST) services/analysis-service/tests/test_*.py -v -k "integration"

.PHONY: test-luck-pillars
test-luck-pillars:
	PYTHONPATH=$(PYTHONPATH) $(PYTEST) services/analysis-service/tests/test_luck_pillars_engine.py -v

.PHONY: test-ten-gods
test-ten-gods:
	PYTHONPATH=$(PYTHONPATH) $(PYTEST) services/analysis-service/tests/test_ten_gods_engine.py -v

.PHONY: test-twelve-stages
test-twelve-stages:
	PYTHONPATH=$(PYTHONPATH) $(PYTEST) services/analysis-service/tests/test_twelve_stages.py -v

.PHONY: test-coverage
test-coverage:
	PYTHONPATH=$(PYTHONPATH) $(PYTEST) services/analysis-service/tests/ --cov=services/analysis-service/app --cov-report=html --cov-report=term

.PHONY: lint
lint:
	$(PYTHON) -m ruff check services/ || true

.PHONY: format
format:
	$(PYTHON) -m ruff format services/ || true

.PHONY: typecheck
typecheck:
	$(PYTHON) -m mypy services/analysis-service/app/ || true

.PHONY: venv
venv:
	python3.12 -m venv .venv
	.venv/bin/pip install --upgrade pip setuptools wheel
	@echo "✅ Virtual environment created at .venv"
	@echo "Install dependencies: .venv/bin/pip install -r requirements.txt"

.PHONY: clean
clean:
	rm -rf .venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	@echo "✅ Cleaned all caches and venv"

.PHONY: verify-python
verify-python:
	@echo "Verifying Python version..."
	@$(PYTHON) --version
	@$(PYTHON) -c "import sys; assert sys.version_info[:2] == (3, 12), f'Expected Python 3.12, got {sys.version_info[:2]}'"
	@echo "✅ Python 3.12.x confirmed"

.PHONY: verify-deps
verify-deps:
	@echo "Checking installed packages..."
	@$(PYTHON) -m pip list | grep -E "(pytest|pydantic|fastapi)" || echo "❌ Missing dependencies"

.PHONY: dev-setup
dev-setup: verify-python
	@echo "Setting up development environment..."
	@if [ ! -d ".venv" ]; then \
		echo "Creating venv..."; \
		python3.12 -m venv .venv; \
	fi
	@echo "Installing dependencies..."
	@.venv/bin/pip install --upgrade pip setuptools wheel
	@if [ -f "requirements.txt" ]; then \
		.venv/bin/pip install -r requirements.txt; \
	fi
	@echo "✅ Development environment ready"
