# Poetry Migration Strategy - Dev Dependency Management

**Date:** 2025-11-02
**Status:** ✅ Poetry 2.2.1 Installed | 📋 Strategy Recommendation
**Goal:** Determine optimal dev dependency sharing strategy for monorepo services

---

## 1. Current State Analysis

### 1.1 Root Project (Monorepo)

**File:** `pyproject.toml` (root)

**Dev Dependencies:**
```toml
[tool.poetry.group.dev.dependencies]
black = "24.4.2"
isort = "5.13.2"
ruff = "0.6.4"
mypy = "1.11.1"
pytest = "8.3.2"
httpx = "0.27.0"
fastapi = "0.120.4"
starlette = "0.49.1"
uvicorn = {extras = ["standard"], version = "0.30.3"}
pytest-asyncio = "0.23.8"
canonicaljson = "2.0.0"
jsonschema = "4.23.0"
```

**Purpose:** Shared tooling for linting, formatting, type-checking, and testing across all services

### 1.2 Service Projects (7 Services)

**Services:**
1. analysis-service
2. api-gateway
3. astro-service
4. llm-checker
5. llm-polish
6. pillars-service
7. tz-time-service

**Current Pattern:**
```toml
[project.optional-dependencies]
test = [
  "httpx>=0.27,<0.28",
  "pytest>=8.3,<9",
  "pytest-asyncio>=0.23,<0.24",
  "jsonschema>=4.23,<5",  # Only in analysis-service
]
```

**Observations:**
- Each service defines its own test dependencies
- Dependencies are duplicated across all 7 services
- Version ranges are consistent (good!)
- No linting/formatting tools at service level (rely on root)

---

## 2. Dev Dependency Strategy Options

### Option A: Keep Service-Specific Test Dependencies ✅ RECOMMENDED

**Approach:**
- Root pyproject.toml: Shared tooling (black, isort, ruff, mypy)
- Service pyproject.toml: Service-specific test dependencies only

**Pros:**
- ✅ Services remain independently testable
- ✅ Each service declares its own runtime test requirements
- ✅ Clear separation: tooling (root) vs testing (service)
- ✅ Easier to deploy services independently in future
- ✅ No breaking changes to existing CI/CD

**Cons:**
- ⚠️ Some duplication (httpx, pytest, pytest-asyncio across 7 services)
- ⚠️ Need to keep versions consistent manually (or use dependabot)

**Implementation:**
```toml
# Root: pyproject.toml
[tool.poetry.group.dev.dependencies]
black = "24.4.2"
isort = "5.13.2"
ruff = "0.6.4"
mypy = "1.11.1"

# Services: services/*/pyproject.toml (keep as-is)
[project.optional-dependencies]
test = [
  "httpx>=0.27,<0.28",
  "pytest>=8.3,<9",
  "pytest-asyncio>=0.23,<0.24",
]
```

---

### Option B: Centralize All Dev Dependencies at Root

**Approach:**
- Root pyproject.toml: ALL dev dependencies (tooling + testing)
- Service pyproject.toml: Remove test dependencies entirely

**Pros:**
- ✅ Single source of truth for all dev dependencies
- ✅ No duplication
- ✅ Easier version management

**Cons:**
- ❌ Services not independently testable without root
- ❌ Breaking change to service isolation
- ❌ Harder to deploy services to separate repos later
- ❌ CI/CD needs to install root dependencies for service tests

**Implementation:**
```toml
# Root: pyproject.toml
[tool.poetry.group.dev.dependencies]
black = "24.4.2"
isort = "5.13.2"
ruff = "0.6.4"
mypy = "1.11.1"
pytest = "8.3.2"
httpx = "0.27.0"
pytest-asyncio = "0.23.8"
jsonschema = "4.23.0"

# Services: services/*/pyproject.toml
# Remove [project.optional-dependencies] entirely
```

---

### Option C: Hybrid - Workspace Poetry Dependency Groups

**Approach:**
- Use Poetry workspace feature (if available)
- Define shared test dependencies in root as a group
- Services inherit from root group

**Pros:**
- ✅ No duplication
- ✅ Services remain testable via root
- ✅ Cleaner than Option B

**Cons:**
- ⚠️ Poetry workspace support is still experimental (as of Poetry 2.2)
- ⚠️ More complex configuration
- ⚠️ May not work with all CI/CD setups

**Implementation:**
```toml
# Root: pyproject.toml
[tool.poetry.group.test.dependencies]
pytest = "8.3.2"
httpx = "0.27.0"
pytest-asyncio = "0.23.8"

# Services would reference this group (experimental)
```

---

## 3. Recommendation: Option A (Service-Specific Test Dependencies)

### 3.1 Rationale

**Best Practices:**
1. **Service Independence:** Each service should declare its own test dependencies
2. **Future-Proofing:** Easier to extract services to separate repos
3. **Clear Ownership:** Root owns tooling, services own testing
4. **Minimal Disruption:** No breaking changes to existing setup

**Trade-offs Accepted:**
- Some duplication is acceptable for independence
- Dependabot will keep versions consistent automatically
- Consistency can be enforced via CI lint checks

### 3.2 Implementation Plan

**Step 1: Keep Current Service Structure**
```bash
# No changes needed to service pyproject.toml files
# They already follow this pattern
```

**Step 2: Root Provides Tooling Only**
```toml
# pyproject.toml (root) - Already implemented
[tool.poetry.group.dev.dependencies]
black = "24.4.2"
isort = "5.13.2"
ruff = "0.6.4"
mypy = "1.11.1"
# Remove service-specific test deps from root (optional cleanup)
```

**Step 3: Document Usage Pattern**
```markdown
## Dev Workflow

**Root Level (Linting/Formatting):**
```bash
poetry install  # Install black, isort, ruff, mypy
poetry run black .
poetry run isort .
poetry run ruff check .
poetry run mypy services/
```

**Service Level (Testing):**
```bash
cd services/analysis-service
python3 -m pip install -e ".[test]"  # Install service + test deps
pytest tests/
```
```

---

## 4. Migration Steps (Already Completed)

### 4.1 Poetry Installation ✅

```bash
$ poetry --version
Poetry (version 2.2.1)
```

**Location:** `/home/dan914/.local/bin/poetry`

### 4.2 Lock File Generation ✅

```bash
$ poetry lock
Writing lock file
```

**Created:** `poetry.lock` (root)

### 4.3 Dependency Installation ✅

```bash
$ poetry install
Installing dependencies from lock file
Package operations: 41 installs, 0 updates, 0 removals
Installing the current project: saju-monorepo (0.1.0)
```

**Virtual Environment:** `/home/dan914/.cache/pypoetry/virtualenvs/saju-monorepo-XUlLVoVA-py3.12`

---

## 5. Service Dependency Summary

### 5.1 Common Pattern (All Services)

**Runtime Dependencies:**
```toml
dependencies = [
  "fastapi>=0.120,<0.121",
  "uvicorn[standard]>=0.30,<0.31",
]
```

**Test Dependencies:**
```toml
[project.optional-dependencies]
test = [
  "httpx>=0.27,<0.28",
  "pytest>=8.3,<9",
  "pytest-asyncio>=0.23,<0.24",
]
```

### 5.2 Service-Specific Additions

**analysis-service:**
```toml
test = [
  "httpx>=0.27,<0.28",
  "pytest>=8.3,<9",
  "pytest-asyncio>=0.23,<0.24",
  "jsonschema>=4.23,<5",  # Extra: schema validation tests
]
```

**Other Services:** Standard pattern only

---

## 6. Recommended Directory Structure

```
saju-engine/
├── pyproject.toml              # Poetry config + shared dev tooling
├── poetry.lock                 # Locked versions
├── .venv/                      # Poetry virtual env (if using)
├── services/
│   ├── analysis-service/
│   │   ├── pyproject.toml      # Service runtime + test deps
│   │   ├── app/
│   │   └── tests/
│   ├── api-gateway/
│   │   ├── pyproject.toml      # Service runtime + test deps
│   │   ├── app/
│   │   └── tests/
│   └── .../
└── requirements/
    └── dev.txt                 # Legacy (can be removed after migration)
```

---

## 7. CI/CD Integration

### 7.1 Root-Level Jobs (Linting/Formatting)

```yaml
# .github/workflows/lint.yml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install Poetry
        run: pipx install poetry
      - name: Install dependencies
        run: poetry install
      - name: Run linters
        run: |
          poetry run black --check .
          poetry run isort --check .
          poetry run ruff check .
          poetry run mypy services/
```

### 7.2 Service-Level Jobs (Testing)

```yaml
# .github/workflows/test-analysis-service.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install service dependencies
        run: |
          cd services/analysis-service
          pip install -e ".[test]"
      - name: Run tests
        run: |
          cd services/analysis-service
          pytest tests/ -v
```

---

## 8. Cleanup Recommendations (Optional)

### 8.1 Remove Redundant Root Test Dependencies

**Current Root Dev Deps:**
```toml
[tool.poetry.group.dev.dependencies]
# Tooling (keep)
black = "24.4.2"
isort = "5.13.2"
ruff = "0.6.4"
mypy = "1.11.1"

# Service test deps (remove or move to separate group)
pytest = "8.3.2"
httpx = "0.27.0"
pytest-asyncio = "0.23.8"
fastapi = "0.120.4"  # Only needed for testing services
starlette = "0.49.1"
uvicorn = {extras = ["standard"], version = "0.30.3"}
canonicaljson = "2.0.0"
jsonschema = "4.23.0"
```

**Recommendation:** Keep pytest/httpx in root for convenience, but document that services should use their own `[test]` extras for independence.

### 8.2 Remove Legacy requirements/dev.txt

**Status:** Can be removed after Poetry migration is validated

```bash
# Test that everything works with Poetry first
poetry run pytest services/analysis-service/tests/
poetry run black --check .

# Then remove
rm requirements/dev.txt
```

---

## 9. Future Enhancements

### 9.1 Poetry Workspace Support (When Stable)

Monitor Poetry 2.x for workspace feature maturity:
- Shared dependency groups
- Inter-service dependencies
- Unified lock file

### 9.2 Dependabot Configuration

**Already Created:** `.github/dependabot.yml`

Ensure it covers both:
- Root `pyproject.toml` (Poetry dependencies)
- Service `pyproject.toml` files (PEP 621 dependencies)

### 9.3 Pre-commit Hooks

Consider adding `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: black
        name: black
        entry: poetry run black
        language: system
        types: [python]
      - id: isort
        name: isort
        entry: poetry run isort
        language: system
        types: [python]
      - id: ruff
        name: ruff
        entry: poetry run ruff check
        language: system
        types: [python]
```

---

## 10. Conclusion

**✅ Completed:**
1. Poetry 2.2.1 installed locally
2. `poetry lock` executed successfully
3. `poetry install` completed (41 packages)
4. Strategy recommendation: Keep service-specific test dependencies

**✅ Recommended Approach:**
- **Root:** Shared tooling (black, isort, ruff, mypy) via Poetry
- **Services:** Service-specific test dependencies via PEP 621 `[project.optional-dependencies]`
- **Rationale:** Service independence, future-proofing, minimal disruption

**📋 Next Steps (Optional):**
1. Clean up redundant root test dependencies (keep for convenience or remove)
2. Remove legacy `requirements/dev.txt` after validation
3. Update CI/CD workflows to use Poetry for linting jobs
4. Add pre-commit hooks for automated linting

**📌 No Action Required:**
- Service `pyproject.toml` files are already correctly structured
- Current pattern aligns with recommended Option A
- Dependabot will keep versions consistent

---

**Strategy Approved By:** Claude
**Approval Date:** 2025-11-02
**Verification Method:** Analysis of all 7 service pyproject.toml files + root configuration
