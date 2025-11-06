# 🧠 Ultrathink: Python Version Enforcement Strategy

**Date:** 2025-10-12 KST
**Issue:** Multiple Python versions causing import/decorator failures
**Goal:** Single source of truth → Python 3.12.11 everywhere

---

## 🔍 Current State Analysis

### Environment Audit

**System Pythons Found:**
```bash
# System Python (Homebrew)
/opt/homebrew/bin/python3 → Python 3.13.x

# Venv Python (correct)
.venv/bin/python3 → Python 3.12.11
```

**Current Problems:**
1. ❌ No `.python-version` file → pyenv/asdf can't enforce version
2. ❌ Scripts use `#!/usr/bin/env python3` → May pick system Python 3.13
3. ❌ Tests sometimes run outside venv → Import path chaos
4. ❌ No CI configuration file → GitHub Actions may use wrong version
5. ❌ No helper script → Easy to accidentally use system Python
6. ❌ No guardrails → Silent failures when wrong Python is used

### Why This Matters

**The @dataclass Failure:**
- System Python 3.13 was used instead of venv Python 3.12.11
- Dynamic import failed because module not in `sys.modules`
- Took multiple attempts to diagnose and fix

**Future Risk:**
- Different team members may have Python 3.11, 3.12, 3.13
- CI/CD may use Python 3.10 by default
- Pre-commit hooks may use wrong interpreter
- Production deployment may use different version

---

## ✅ Solution Architecture

### 1. Source of Truth: .python-version

```bash
# .python-version (pyenv/asdf)
3.12.11
```

**Benefits:**
- pyenv automatically switches to 3.12.11 when entering directory
- asdf respects this file
- Single line, zero ambiguity
- Version-controlled alongside code

### 2. Helper Script: scripts/py

```bash
#!/bin/bash
# scripts/py - Proxy to venv Python with safety checks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"

# Check if venv exists
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "❌ Virtual environment not found at $VENV_PYTHON"
    echo "Run: python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check Python version
VERSION=$("$VENV_PYTHON" --version 2>&1 | awk '{print $2}')
if [[ ! "$VERSION" =~ ^3\.12\. ]]; then
    echo "❌ Expected Python 3.12.x, but got $VERSION"
    echo "Rebuild venv: rm -rf .venv && python3.12 -m venv .venv"
    exit 1
fi

# Forward all arguments to venv Python
exec "$VENV_PYTHON" "$@"
```

**Usage:**
```bash
./scripts/py -m pytest tests/
./scripts/py scripts/calculate_pillars.py
./scripts/py -c "import sys; print(sys.version)"
```

### 3. Makefile: Standardized Commands

```makefile
# Makefile

PYTHON := ./scripts/py
PYTEST := $(PYTHON) -m pytest

.PHONY: test
test:
	$(PYTEST) services/analysis-service/tests/ -v

.PHONY: test-unit
test-unit:
	$(PYTEST) services/analysis-service/tests/test_*.py -v -k "not integration"

.PHONY: test-integration
test-integration:
	$(PYTEST) services/analysis-service/tests/test_*.py -v -k "integration"

.PHONY: test-luck-pillars
test-luck-pillars:
	$(PYTEST) services/analysis-service/tests/test_luck_pillars_engine.py -v

.PHONY: lint
lint:
	$(PYTHON) -m ruff check services/

.PHONY: format
format:
	$(PYTHON) -m ruff format services/

.PHONY: typecheck
typecheck:
	$(PYTHON) -m mypy services/analysis-service/app/

.PHONY: venv
venv:
	python3.12 -m venv .venv
	.venv/bin/pip install --upgrade pip setuptools wheel
	.venv/bin/pip install -r requirements.txt

.PHONY: clean
clean:
	rm -rf .venv
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

### 4. CI Configuration: .github/workflows/tests.yml

```yaml
name: Tests

on:
  push:
    branches: [main, docs/prompts-freeze-v1]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.12.11'

      - name: Cache venv
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-3.12.11-${{ hashFiles('requirements.txt') }}

      - name: Create virtual environment
        run: |
          python3.12 -m venv .venv
          .venv/bin/pip install --upgrade pip
          .venv/bin/pip install -r requirements.txt

      - name: Run tests
        run: |
          make test

      - name: Upload coverage
        if: always()
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
```

### 5. Guardrails: pre-commit Configuration

```yaml
# .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: check-python-version
        name: Check Python version
        entry: bash -c 'if [[ -z "$VIRTUAL_ENV" ]]; then echo "❌ Not in virtual environment. Run: source .venv/bin/activate"; exit 1; fi; VERSION=$(python --version | awk "{print \$2}"); if [[ ! "$VERSION" =~ ^3\.12\. ]]; then echo "❌ Wrong Python version: $VERSION (expected 3.12.x)"; exit 1; fi'
        language: system
        pass_filenames: false

      - id: pytest-check
        name: Run pytest
        entry: ./scripts/py -m pytest services/analysis-service/tests/ -x
        language: system
        types: [python]
        pass_filenames: false
        stages: [commit]
```

### 6. direnv Configuration (Optional)

```bash
# .envrc

# Auto-activate venv when entering directory
layout python python3.12

# Set PYTHONPATH
export PYTHONPATH=".:services/analysis-service:services/common"

# Shortcuts
alias py="./scripts/py"
alias pytest="./scripts/py -m pytest"
```

---

## 📋 Implementation Plan

### Phase 1: Version Enforcement (10 min)

1. **Create `.python-version`**
   ```bash
   echo "3.12.11" > .python-version
   ```

2. **Create `scripts/py` helper**
   - Implement version check
   - Make executable: `chmod +x scripts/py`

3. **Verify venv**
   ```bash
   .venv/bin/python3 --version  # Should be 3.12.11
   ```

### Phase 2: Standardize Commands (15 min)

4. **Create `Makefile`**
   - `make test` → Run all tests via venv
   - `make test-luck-pillars` → Run specific test
   - `make venv` → Rebuild venv from scratch

5. **Update shebangs in scripts/**
   ```bash
   # Find all Python scripts
   find scripts/ -name "*.py" -type f

   # Update shebangs to use helper
   # FROM: #!/usr/bin/env python3
   # TO:   #!/usr/bin/env -S ../scripts/py
   ```

6. **Update test scripts**
   ```bash
   # Replace hardcoded python3 calls
   sed -i '' 's/python3 /\.\/scripts\/py /g' test_*.py
   ```

### Phase 3: CI/CD Integration (10 min)

7. **Create `.github/workflows/tests.yml`**
   - Pin to Python 3.12.11
   - Use venv for all steps
   - Cache venv for speed

8. **Test CI locally** (optional)
   ```bash
   # Using act (https://github.com/nektos/act)
   act -j test
   ```

### Phase 4: Documentation (5 min)

9. **Update README.md**
   ```markdown
   ## Development Setup

   **Python Version:** 3.12.11 (enforced)

   1. Install Python 3.12.11 (via pyenv or system)
   2. Create venv: `make venv`
   3. Run tests: `make test`
   4. Run scripts: `./scripts/py <script_name>`

   **Note:** All commands must use `./scripts/py` or `make` targets.
   Direct `python3` calls may use wrong version.
   ```

10. **Create DEVELOPMENT.md**
    - Python version policy
    - Venv management
    - Common commands
    - Troubleshooting

### Phase 5: Guardrails (Optional, 10 min)

11. **Setup pre-commit**
    ```bash
    ./scripts/py -m pip install pre-commit
    ./scripts/py -m pre_commit install
    ```

12. **Setup direnv** (if team uses it)
    ```bash
    brew install direnv
    echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
    direnv allow .
    ```

---

## 🔬 Verification Checklist

After implementation:

- [ ] `.python-version` exists and contains `3.12.11`
- [ ] `scripts/py` is executable and checks version
- [ ] `make test` runs all tests via venv
- [ ] CI workflow pins to 3.12.11
- [ ] All scripts use `./scripts/py` shebang or are invoked via `make`
- [ ] `test_luck_pillars_standalone.py` updated to use `./scripts/py`
- [ ] README documents Python version requirement
- [ ] Team members can reproduce environment

### Test Commands

```bash
# 1. Version check
./scripts/py --version
# Expected: Python 3.12.11

# 2. Run tests via Makefile
make test
# Expected: All tests pass using venv Python

# 3. Run luck pillars test
make test-luck-pillars
# Expected: 3/3 passing

# 4. Run standalone integration test
./scripts/py test_luck_pillars_standalone.py
# Expected: All ✅

# 5. Verify PYTHONPATH is set correctly
./scripts/py -c "import sys; print('\\n'.join(sys.path))"
# Expected: services/analysis-service and services/common in path

# 6. Check no system Python leakage
which python3
# Expected: /usr/bin/python3 or /opt/homebrew/bin/python3 (NOT used)

./scripts/py -c "import sys; print(sys.executable)"
# Expected: /Users/.../사주/.venv/bin/python3
```

---

## 🎯 Benefits After Implementation

### For Developers

✅ **No ambiguity**: One command works for everyone
✅ **Auto-verification**: Scripts fail fast if wrong Python
✅ **Muscle memory**: `./scripts/py <script>` or `make <target>`
✅ **Onboarding**: New devs see version requirement immediately

### For CI/CD

✅ **Reproducibility**: Same Python version as local
✅ **Caching**: Venv cached by Python version + requirements hash
✅ **Fast feedback**: Tests run in <2 minutes with cache

### For Production

✅ **Docker alignment**: Dockerfile can use same `3.12.11`
✅ **No surprises**: Behavior identical to dev/test
✅ **Dependency lock**: requirements.txt pins exact versions

---

## 📊 Comparison: Before vs After

| Scenario | Before | After |
|----------|--------|-------|
| Run tests | `python3 -m pytest` (may use 3.13) | `make test` (always 3.12.11) |
| Run script | `python3 scripts/foo.py` (may fail) | `./scripts/py scripts/foo.py` (guaranteed) |
| CI version | Unspecified (varies by runner) | `3.12.11` (explicit) |
| New dev setup | "Install Python somehow" | "See .python-version, run make venv" |
| Version drift | Silent failures | Loud errors with fix instructions |

---

## 🚀 Rollout Strategy

### Week 1: Core Team
1. Implement Phase 1-2 (version enforcement + Makefile)
2. Update all scripts to use `./scripts/py`
3. Document in README
4. Test locally

### Week 2: CI/CD
1. Add `.github/workflows/tests.yml`
2. Verify tests pass in CI
3. Add badge to README

### Week 3: Guardrails
1. Setup pre-commit hooks (optional)
2. Add direnv support (optional)
3. Monitor for issues

### Communication

**Slack/Email announcement:**
> 🚨 Python Version Update
>
> We've standardized on **Python 3.12.11** for all development.
>
> **Action Required:**
> 1. `git pull` to get .python-version
> 2. `make venv` to rebuild virtual environment
> 3. Use `make test` instead of direct `pytest`
> 4. Use `./scripts/py` for all Python scripts
>
> See README.md for details. Questions? Ask in #dev-saju

---

## 🔧 Troubleshooting

### "python3.12: command not found"

**On macOS:**
```bash
brew install python@3.12
```

**On Ubuntu:**
```bash
sudo apt-add-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv
```

**Using pyenv:**
```bash
pyenv install 3.12.11
pyenv local 3.12.11
```

### "Wrong Python version in venv"

```bash
# Rebuild venv
rm -rf .venv
make venv
```

### "Tests failing with import errors"

```bash
# Check PYTHONPATH
./scripts/py -c "import sys; print(sys.path)"

# Should include:
# - /Users/.../사주/services/analysis-service
# - /Users/.../사주/services/common
```

### "CI tests failing"

Check:
1. `.github/workflows/tests.yml` has `python-version: '3.12.11'`
2. Cache key includes Python version
3. Venv is activated before running tests

---

**Analysis Complete**
**Estimated Implementation Time:** 50 minutes
**Impact:** High (prevents all future version-related issues)
**Priority:** Critical (do before Phase 2 completion report)
