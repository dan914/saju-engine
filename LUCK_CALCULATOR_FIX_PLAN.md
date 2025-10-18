# LuckCalculator Fix Plan - What We Need

**Date:** 2025-10-10
**Status:** Ready to implement - all pieces exist

---

## What We Need

### 1. **A SolarTermLoader that loads from CSV files**

LuckCalculator needs:
```python
loader = SolarTermLoader(data_path="/path/to/data/")
entries = loader.load_year(2000)  # Returns list of TermEntry objects
# Each entry must have: entry.term, entry.utc_time
```

### 2. **LuckCalculator needs to expose a method the orchestrator can call**

Orchestrator tries to call (in order):
1. `compute()`
2. `compute_start_age()`
3. `run()`
4. `__call__()`

Current LuckCalculator only has `compute_start_age(ctx: LuckContext)` which doesn't match.

---

## What We Already Have ✅

### 1. **CSV Solar Term Data** (1900-2050+)
**Location:** `/data/terms_*.csv`

**Format:**
```csv
term,lambda_deg,utc_time,delta_t_seconds,source,algo_version
小寒,0,2000-01-06T00:56:26Z,62.93,SAJU_LITE_REFINED,v1.5.10+astro
立春,30,2000-02-04T12:35:59Z,62.96,SAJU_LITE_REFINED,v1.5.10+astro
```

**Coverage:** 150+ years of precise solar term data ✅

### 2. **Working CSV Loader Implementation**
**Location:** `services/astro-service/app/core/loader.py`

**Code:**
```python
@dataclass(slots=True)
class SolarTermLoader:
    table_path: Path

    def load_year(self, year: int) -> Iterable[TermEntry]:
        file_path = self.table_path / f"terms_{year}.csv"
        with file_path.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                utc_time = datetime.fromisoformat(row["utc_time"].replace("Z", "+00:00"))
                yield TermEntry(
                    term=row["term"],
                    lambda_deg=float(row["lambda_deg"]),
                    utc_time=utc_time,
                    ...
                )
```

**Status:** ✅ Already exists and works in astro-service

### 3. **TermEntry Model**
**Location:** `services/astro-service/app/models/terms.py`

**Code:**
```python
class TermEntry(BaseModel):
    term: str
    lambda_deg: float
    utc_time: datetime
    local_time: datetime
    delta_t_seconds: float
    source: str
    algo_version: str
```

**Status:** ✅ Pydantic model ready to use

---

## The Fix (Option A - Recommended: 30 minutes)

### Step 1: Copy SolarTermLoader to saju_common

**Create:** `services/common/saju_common/file_solar_term_loader.py`

```python
"""File-based solar term loader for CSV data."""
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

@dataclass(slots=True)
class SolarTermEntry:
    """Simplified solar term entry for luck calculation."""
    term: str
    utc_time: datetime

@dataclass(slots=True)
class FileSolarTermLoader:
    """Loads solar terms from CSV files in data/ directory."""

    table_path: Path

    def load_year(self, year: int) -> Iterable[SolarTermEntry]:
        """Yield solar term entries for the given year."""
        file_path = self.table_path / f"terms_{year}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Solar term data missing for {year}")

        with file_path.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                utc_time = datetime.fromisoformat(row["utc_time"].replace("Z", "+00:00"))
                yield SolarTermEntry(
                    term=row["term"],
                    utc_time=utc_time
                )
```

**Effort:** Copy + simplify existing code (5 minutes)

### Step 2: Export from saju_common

**Update:** `services/common/saju_common/__init__.py`

```python
from .file_solar_term_loader import FileSolarTermLoader, SolarTermEntry

__all__ = [
    # ... existing exports ...
    "FileSolarTermLoader",
    "SolarTermEntry",
]
```

**Effort:** 1 minute

### Step 3: Update luck.py to use FileSolarTermLoader

**Update:** `services/analysis-service/app/core/luck.py` (line 16, 39)

```python
# Line 16 - Change import
from saju_common import FileSolarTermLoader as SimpleSolarTermLoader

# Line 39 - No change needed, already passes TERM_DATA_PATH
self._term_loader = SimpleSolarTermLoader(TERM_DATA_PATH)
```

**Effort:** 2 minutes

### Step 4: Add wrapper method for orchestrator

**Update:** `services/analysis-service/app/core/luck.py` (add after line 83)

```python
def compute(self, pillars: Dict[str, str], birth_dt: str, gender: str,
            timezone: str = "Asia/Seoul") -> Dict[str, Any]:
    """Wrapper for orchestrator compatibility.

    Returns combined start_age + direction results.
    """
    # Parse birth_dt
    if isinstance(birth_dt, str):
        birth_dt = datetime.fromisoformat(birth_dt.replace('Z', '+00:00'))

    ctx = LuckContext(
        local_dt=birth_dt,
        timezone=timezone,
        gender=gender
    )

    start_age = self.compute_start_age(ctx)
    direction = self.luck_direction(ctx)

    return {
        **start_age,      # start_age, prev_term, next_term, interval_days
        **direction,      # direction, method, sex_at_birth
    }
```

**Effort:** 5 minutes

### Step 5: Test

```python
from app.core.luck import LuckCalculator

calc = LuckCalculator()
result = calc.compute(
    pillars={"year": "庚辰", "month": "乙酉", "day": "癸酉", "hour": "丁巳"},
    birth_dt="2000-09-14T10:00:00",
    gender="M",
    timezone="Asia/Seoul"
)
print(result)
# Expected:
# {
#   "start_age": 8.2,
#   "prev_term": "白露",
#   "next_term": "秋分",
#   "interval_days": 24.6,
#   "days_from_prev": 3.4,
#   "direction": "forward",
#   "method": "traditional_sex",
#   "sex_at_birth": "M"
# }
```

**Effort:** 5 minutes

**Total Time:** ~20-30 minutes

---

## Alternative Option B: Quick Stub (5 minutes)

If you just want to unblock orchestrator testing immediately:

**Create stub LuckCalculator.compute():**

```python
def compute(self, pillars: Dict[str, str], birth_dt: str, gender: str,
            timezone: str = "Asia/Seoul") -> Dict[str, Any]:
    """Stub implementation - returns placeholder data."""
    direction = "forward" if gender in ("M", "male") else "reverse"
    return {
        "start_age": 8.0,
        "prev_term": "未知",
        "next_term": "未知",
        "interval_days": 24.0,
        "days_from_prev": 0.0,
        "direction": direction,
        "method": "traditional_sex",
        "sex_at_birth": gender,
        "note": "STUB - solar term calculation not implemented"
    }
```

**Pros:**
- 5 minutes
- Unblocks orchestrator immediately
- Can test everything else

**Cons:**
- Start age is fake
- Not production-ready

---

## Comparison

| Aspect | Option A (FileSolarTermLoader) | Option B (Stub) |
|--------|-------------------------------|-----------------|
| **Time** | 30 minutes | 5 minutes |
| **Accuracy** | ✅ Real solar term data | ❌ Fake placeholder |
| **Production Ready** | ✅ Yes | ❌ No |
| **Unblocks Testing** | ✅ Yes | ✅ Yes |
| **Code Reuse** | ✅ Uses existing astro loader | ❌ Throwaway code |
| **Maintenance** | ✅ Clean, permanent solution | ⚠️ Technical debt |

---

## Recommendation

**Implement Option A (FileSolarTermLoader)** - 30 minutes well spent

**Why:**
1. We already have all the pieces (CSV data + working loader)
2. 30 minutes is minimal time investment
3. Production-ready immediately
4. No technical debt
5. Clean architecture (saju_common provides file loading)

**Only use Option B if:**
- Need to demo in next 10 minutes
- Solar term accuracy not critical for current test

---

## Summary

**What we need:**
1. ✅ CSV solar term data (HAVE - 150 years in /data/)
2. ✅ CSV loader (HAVE - in astro-service/loader.py)
3. ✅ TermEntry model (HAVE - in astro-service/models/)
4. ❌ Integration to luck.py (NEED - 30 min to implement)

**The fix:**
- Copy 30 lines of CSV loading code
- Add 15-line wrapper method
- Test with real data

**Result:**
- Orchestrator fully working with real engines
- Production-ready luck calculation
- No technical debt

---

**Ready to implement?** All required components exist. Just need to wire them together.
