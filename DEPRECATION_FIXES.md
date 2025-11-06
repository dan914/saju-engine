# FastAPI & Python Deprecation Fixes

Quick reference guide for resolving deprecation warnings in the saju-engine project.

---

## 1. FastAPI `@app.on_event("startup")` → Lifespan Pattern

**Affected Files:** (4 services)
- `services/analysis-service/app/main.py:34`
- `services/astro-service/app/main.py:33`
- `services/pillars-service/app/main.py:23`
- `services/tz-time-service/app/main.py:23`

### Current Pattern ❌
```python
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def load_policies():
    logger.info("Loading policies...")

@app.on_event("shutdown")
async def cleanup():
    logger.info("Cleaning up...")
```

### Recommended Pattern ✅
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Loading policies...")
    yield
    # Shutdown logic
    logger.info("Cleaning up...")

app = FastAPI(lifespan=lifespan)
```

### Example: analysis-service/app/main.py

**Before:**
```python
@app.on_event("startup")
async def load_policies():
    """Load policy files on startup to validate they exist."""
    logger.info("Loading policies on startup...")
    try:
        # Existing policy loading logic
        load_policy_json("strength_policy_v2.json")
        load_policy_json("relation_policy.json")
        # ... more policies
        logger.info("All policies loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load policies: {e}")
        raise
```

**After:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Loading policies on startup...")
    try:
        load_policy_json("strength_policy_v2.json")
        load_policy_json("relation_policy.json")
        # ... more policies
        logger.info("All policies loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load policies: {e}")
        raise

    yield  # Application runs here

    # Shutdown (if needed)
    logger.info("Shutting down...")

app = FastAPI(
    title="Analysis Service",
    version="1.2.0",
    lifespan=lifespan,  # ✅ Use lifespan parameter
)
```

---

## 2. Python `datetime.utcnow()` → `datetime.now(timezone.utc)`

**Affected Files:** (1 file)
- `services/analysis-service/app/core/master_orchestrator_real.py:229`

### Current Pattern ❌
```python
from datetime import datetime

"timestamp": datetime.utcnow().isoformat() + "Z"
```

### Recommended Pattern ✅
```python
from datetime import datetime, timezone

"timestamp": datetime.now(timezone.utc).isoformat()
```

### Example: master_orchestrator_real.py

**Before:**
```python
from datetime import datetime

enriched["meta"] = {
    "orchestrator_version": "1.2.0",
    "timestamp": datetime.utcnow().isoformat() + "Z",  # ❌ Deprecated
}
```

**After:**
```python
from datetime import datetime, timezone

enriched["meta"] = {
    "orchestrator_version": "1.2.0",
    "timestamp": datetime.now(timezone.utc).isoformat(),  # ✅ Timezone-aware
}
```

**Note:** `datetime.now(timezone.utc)` automatically includes timezone info (`+00:00`), so no need to manually append `"Z"`.

---

## 3. Pydantic v2 `allow_population_by_field_name` → `populate_by_name`

**Affected Files:** (implicit via Pydantic models)
- `services/pillars-service/app/models/*.py` (if Config class used)

### Current Pattern ❌
```python
from pydantic import BaseModel

class MyModel(BaseModel):
    some_field: str

    class Config:
        allow_population_by_field_name = True  # ❌ Pydantic v1 name
```

### Recommended Pattern ✅
```python
from pydantic import BaseModel, ConfigDict

class MyModel(BaseModel):
    some_field: str

    model_config = ConfigDict(populate_by_name=True)  # ✅ Pydantic v2
```

**Pydantic v2 Migration Guide:**
- [Pydantic v2 Migration](https://docs.pydantic.dev/latest/migration/)
- [ConfigDict Reference](https://docs.pydantic.dev/latest/api/config/)

---

## Migration Checklist

### Phase 1: FastAPI Lifespan (4 services) 🔴 **High Impact**
- [ ] `analysis-service/app/main.py` - Replace `@app.on_event("startup")`
- [ ] `astro-service/app/main.py` - Replace `@app.on_event("startup")`
- [ ] `pillars-service/app/main.py` - Replace `@app.on_event("startup")`
- [ ] `tz-time-service/app/main.py` - Replace `@app.on_event("startup")`

**Estimated Effort:** 30 minutes (straightforward refactor)

### Phase 2: datetime.utcnow() (1 file) 🟡 **Medium Impact**
- [ ] `master_orchestrator_real.py:229` - Replace with `datetime.now(timezone.utc)`

**Estimated Effort:** 5 minutes

### Phase 3: Pydantic Config (as needed) 🟢 **Low Impact**
- [ ] Audit Pydantic models for `Config` class usage
- [ ] Replace with `model_config = ConfigDict(...)`

**Estimated Effort:** Variable (only if warnings appear)

---

## Testing Strategy

### After Each Migration:

1. **Run service tests:**
   ```bash
   cd services/<service-name>
   pytest tests -v
   ```

2. **Verify startup behavior:**
   ```bash
   uvicorn app.main:app --reload
   # Check logs for policy loading messages
   ```

3. **Check deprecation warnings:**
   ```bash
   pytest tests -v -W default::DeprecationWarning
   ```

### Full Regression Suite:
```bash
# From project root
pytest services/analysis-service/tests -v
pytest services/astro-service/tests -v
pytest services/pillars-service/tests -v
pytest services/tz-time-service/tests -v
```

**Expected Result:** All warnings eliminated, zero regressions.

---

## References

### FastAPI
- [Lifespan Events Documentation](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI 0.109 Release Notes](https://fastapi.tiangolo.com/release-notes/#01090)

### Python datetime
- [PEP 615 – Support for IANA Time Zone Database](https://peps.python.org/pep-0615/)
- [Python 3.12 Deprecations](https://docs.python.org/3/whatsnew/3.12.html#deprecated)

### Pydantic
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [ConfigDict API Reference](https://docs.pydantic.dev/latest/api/config/)

---

## Priority Assessment

| Warning Type | Files Affected | Priority | Blocking? | Deadline |
|--------------|----------------|----------|-----------|----------|
| FastAPI lifespan | 4 | 🟡 Low | No | FastAPI 1.0 |
| datetime.utcnow() | 1 | 🟡 Low | No | Python 3.13 |
| Pydantic Config | 0-5 | 🟢 Very Low | No | None |

**Recommendation:** Schedule for next maintenance sprint. Not blocking for production deployment.

---

## Quick Command Reference

```bash
# Find all @app.on_event usages
grep -r "@app.on_event" services/*/app/

# Find all datetime.utcnow() usages
grep -r "datetime.utcnow()" services/*/app/

# Run tests with deprecation warnings visible
pytest tests -v -W default::DeprecationWarning

# Check if lifespan parameter is already used
grep -r "FastAPI(lifespan=" services/*/app/
```

---

**Last Updated:** 2025-01-31
**Status:** Ready for implementation (non-blocking)
