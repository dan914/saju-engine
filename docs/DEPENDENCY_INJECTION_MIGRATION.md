# Dependency Injection Migration Guide (Week 4)

**Date:** 2025-11-06
**Version:** 1.0.0
**Status:** 🟡 In Progress

## Overview

This guide documents the migration from `@lru_cache` singleton patterns to the `saju_common.container.Container` dependency injection system.

**Benefits:**
- ✅ Better testability (easy mocking with `container.override()`)
- ✅ Explicit lifecycle management
- ✅ Type-safe dependency resolution
- ✅ No global state pollution
- ✅ FastAPI Depends() compatible

---

## Migration Pattern

### Before (Old Pattern)
```python
# services/analysis-service/app/api/dependencies.py
from functools import lru_cache
from ..core import AnalysisEngine

@lru_cache(maxsize=1)
def _analysis_engine_singleton() -> AnalysisEngine:
    return AnalysisEngine()

def get_analysis_engine() -> AnalysisEngine:
    return _analysis_engine_singleton()

# Usage in routes
@app.get("/analyze")
def analyze(engine: AnalysisEngine = Depends(get_analysis_engine)):
    return engine.analyze(...)
```

### After (New Pattern)
```python
# services/analysis-service/app/api/dependencies_new.py
from saju_common.container import Container
from ..core import AnalysisEngine

container = Container()

@container.singleton
def get_analysis_engine():
    return AnalysisEngine()

provide_analysis_engine = container.provider("get_analysis_engine")

# Usage in routes
@app.get("/analyze")
def analyze(engine: AnalysisEngine = Depends(provide_analysis_engine)):
    return engine.analyze(...)
```

---

## Step-by-Step Migration

### Step 1: Create `dependencies_new.py`

For each service, create a new file alongside the old `dependencies.py`:

```bash
services/
├── analysis-service/app/api/
│   ├── dependencies.py       # Old (keep for now)
│   └── dependencies_new.py   # New (migration target)
├── astro-service/app/api/
│   ├── dependencies.py       # Old
│   └── dependencies_new.py   # New
└── pillars-service/app/api/
    ├── dependencies.py       # Old
    └── dependencies_new.py   # New
```

### Step 2: Convert Singletons

**Pattern:**
```python
from saju_common.container import Container

container = Container()

@container.singleton
def get_<resource>():
    """Create and cache <Resource> instance."""
    return <Resource>()

# Export provider for FastAPI Depends
provide_<resource> = container.provider("get_<resource>")
```

**Example:**
```python
@container.singleton
def get_analysis_engine():
    return AnalysisEngine()

provide_analysis_engine = container.provider("get_analysis_engine")
```

### Step 3: Convert Nested Dependencies

When dependencies depend on other dependencies, use `container.get()`:

**Before:**
```python
@lru_cache(maxsize=1)
def _solar_term_loader() -> SolarTermLoader:
    return SolarTermLoader(table_path=DEFAULT_TABLE_PATH)

@lru_cache(maxsize=1)
def _solar_term_service() -> SolarTermService:
    return SolarTermService(loader=_solar_term_loader())
```

**After:**
```python
@container.singleton
def get_solar_term_loader():
    return SolarTermLoader(table_path=DEFAULT_TABLE_PATH)

@container.singleton
def get_solar_term_service():
    # Resolve loader dependency from container
    return SolarTermService(loader=container.get("get_solar_term_loader"))
```

### Step 4: Update Routes

**Before:**
```python
from .api.dependencies import get_analysis_engine

@app.get("/analyze")
def analyze(engine: AnalysisEngine = Depends(get_analysis_engine)):
    ...
```

**After:**
```python
from .api.dependencies_new import provide_analysis_engine

@app.get("/analyze")
def analyze(engine: AnalysisEngine = Depends(provide_analysis_engine)):
    ...
```

### Step 5: Update Startup Preloading

**Before:**
```python
from .api.dependencies import preload_dependencies

@app.on_event("startup")
async def startup():
    preload_dependencies()  # Calls all @lru_cache functions
```

**After:**
```python
from .api.dependencies_new import preload_dependencies

@app.on_event("startup")
async def startup():
    preload_dependencies()  # Calls container.preload()
```

### Step 6: Update Tests

**Before (difficult to mock):**
```python
def test_analyze():
    # Hard to override lru_cache singletons
    # Need to use lru_cache.cache_clear() which is global
    from app.api.dependencies import _analysis_engine_singleton
    _analysis_engine_singleton.cache_clear()
    ...
```

**After (easy to mock):**
```python
from app.api.dependencies_new import container

def test_analyze():
    mock_engine = MockAnalysisEngine()
    with container.override("get_analysis_engine", mock_engine):
        # All requests will use mock_engine
        response = client.get("/analyze")
        assert response.status_code == 200
```

### Step 7: Remove Old Dependencies

Once all routes and tests are migrated:

```bash
# Rename new file to replace old
mv services/analysis-service/app/api/dependencies_new.py \
   services/analysis-service/app/api/dependencies.py
```

---

## Service Migration Checklist

### analysis-service ⏳
- [x] Create `dependencies_new.py`
- [ ] Update routes to use `provide_*` functions
- [ ] Update tests to use `container.override()`
- [ ] Update startup hooks
- [ ] Remove old `dependencies.py`

### astro-service ⏳
- [x] Create `dependencies_new.py`
- [ ] Update routes
- [ ] Update tests
- [ ] Update startup hooks
- [ ] Remove old file

### pillars-service ⏳
- [ ] Create `dependencies_new.py`
- [ ] Update routes
- [ ] Update tests
- [ ] Update startup hooks
- [ ] Remove old file

### tz-time-service ⏳
- [ ] Create `dependencies_new.py`
- [ ] Update routes
- [ ] Update tests
- [ ] Update startup hooks
- [ ] Remove old file

---

## Testing Examples

### Example 1: Override Single Dependency
```python
from app.api.dependencies_new import container
from app.core import AnalysisEngine

def test_analyze_with_mock_engine():
    """Test analysis endpoint with mocked engine."""
    mock_engine = Mock(spec=AnalysisEngine)
    mock_engine.analyze.return_value = {"result": "mocked"}

    with container.override("get_analysis_engine", mock_engine):
        response = client.post("/analyze", json={...})
        assert response.json() == {"result": "mocked"}
        mock_engine.analyze.assert_called_once()
```

### Example 2: Override Nested Dependencies
```python
def test_service_with_mocked_loader():
    """Test service with mocked data loader."""
    mock_loader = Mock(spec=SolarTermLoader)
    mock_loader.load.return_value = [...]

    with container.override("get_solar_term_loader", mock_loader):
        # Service will use mocked loader
        service = container.get("get_solar_term_service")
        result = service.process()
        assert result == expected
```

### Example 3: Reset Between Tests
```python
@pytest.fixture(autouse=True)
def reset_container():
    """Reset container before each test."""
    from app.api.dependencies_new import container
    container.reset()
    yield
    container.reset()
```

---

## Benefits Comparison

| Feature | @lru_cache | Container |
|---------|-----------|-----------|
| **Singleton Management** | ✅ Built-in | ✅ Explicit |
| **Testability** | ❌ Difficult (global state) | ✅ Easy (override) |
| **Type Safety** | 🟡 Partial | ✅ Full |
| **Lifecycle Control** | ❌ No control | ✅ Preload/Reset |
| **Dependency Injection** | ❌ Manual wiring | ✅ Automatic |
| **FastAPI Compatible** | ✅ Yes | ✅ Yes |
| **Context Isolation** | ❌ Global | ✅ Per-container |
| **Debugging** | 🟡 Cache inspection | ✅ Clear resolution |

---

## Troubleshooting

### Issue: Import errors after migration
**Solution:** Update all imports from `dependencies` to `dependencies_new`, or rename the file.

### Issue: Tests fail with "Dependency not registered"
**Solution:** Ensure the test imports the correct container and the dependency is registered:
```python
from app.api.dependencies_new import container
# Verify registration
assert "get_analysis_engine" in container._singletons
```

### Issue: Singleton not shared across requests
**Solution:** Ensure you're using `@container.singleton`, not `@container.factory`.

### Issue: Override doesn't take effect
**Solution:** Override must be active in the same scope as the request:
```python
with container.override("dep", mock):
    response = client.get("/endpoint")  # Inside context
# Outside context, override is gone
```

---

## Next Steps

After completing service migrations:

1. **Retire sitecustomize.py** - Remove path hacking workarounds
2. **Create devshell.py** - Provide development shell with preloaded dependencies
3. **Pydantic Settings** - Add configuration management to container
4. **Documentation** - Update service READMEs with new dependency patterns

---

**Migration Owner:** Claude
**Target Completion:** Week 4, Phase 3
**Status:** Dependencies created for analysis-service and astro-service
