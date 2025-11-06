# Task #8 Implementation Plan: Remove Hardcoded Astro Trace

**Task ID:** #8 (HIGH Priority)
**Estimated Effort:** 1-2 hours
**File:** `services/astro-service/app/core/service.py:29-34`
**Status:** Ready for implementation

---

## 1. Problem Analysis

### Current Code (Lines 29-34)
```python
trace = TraceMetadata(
    rule_id="KR_classic_v1.4",
    delta_t_seconds=57.4,  # ❌ HARDCODED
    tz={"iana": query.timezone, "event": "none", "tzdbVersion": "2025a"},  # ❌ HARDCODED tzdbVersion
    astro={"primary": "AstronomyEngine", "diffSeconds": 0.0},  # ❌ HARDCODED values
)
```

### Issues Identified
1. **delta_t_seconds=57.4**: Hardcoded value ignores actual delta_t from solar term entries
2. **tzdbVersion="2025a"**: Hardcoded despite service having `self._tzdb_version` 
3. **astro.primary="AstronomyEngine"**: Should use actual source from CSV ("SAJU_LITE_REFINED")
4. **astro.diffSeconds=0.0**: Placeholder value, should show actual variance

---

## 2. Data Analysis

### Solar Term Data Structure
```csv
term,lambda_deg,utc_time,delta_t_seconds,source,algo_version
小寒,0,2000-01-06T00:56:26Z,62.93,SAJU_LITE_REFINED,v1.5.10+astro
立春,30,2000-02-04T12:35:59Z,62.96,SAJU_LITE_REFINED,v1.5.10+astro
```

### Example Year 2000 Statistics
- **Terms loaded:** 12 (one per month within the year)
- **First term delta_t:** 62.93s
- **Last term delta_t:** 63.23s  
- **Average delta_t:** 63.08s
- **Range:** 62.93s to 63.23s
- **Variation:** 0.30s (very small)
- **Source:** SAJU_LITE_REFINED
- **Algo version:** v1.5.10+astro

### Key Insight
Delta_t varies slightly throughout the year (~0.3s), so using the average is representative for year-level traces.

---

## 3. Solution Design

### Approach: Calculate Statistics from Loaded Entries

**Before calling TraceMetadata:**
1. Compute average delta_t from all entries
2. Compute delta_t range (max - min) to show variation
3. Extract source and algo_version from first entry (all are same)
4. Use service's `self._tzdb_version` instead of hardcoded value

### Pseudocode
```python
def get_terms(self, query: TermQuery) -> TermResponse:
    tz = ZoneInfo(query.timezone)
    entries = [_with_timezone(entry, tz) for entry in self._loader.load_year(query.year)]
    
    # Calculate statistics from entries
    if entries:
        delta_t_values = [e.delta_t_seconds for e in entries]
        avg_delta_t = sum(delta_t_values) / len(delta_t_values)
        delta_t_range = max(delta_t_values) - min(delta_t_values)
        source = entries[0].source
        algo_version = entries[0].algo_version
    else:
        # Fallback for empty results
        avg_delta_t = 0.0
        delta_t_range = 0.0
        source = "unknown"
        algo_version = "unknown"
    
    trace = TraceMetadata(
        rule_id="KR_classic_v1.4",
        delta_t_seconds=avg_delta_t,  # ✅ Computed average
        tz={"iana": query.timezone, "event": "none", "tzdbVersion": self._tzdb_version},  # ✅ From service
        astro={
            "primary": source,  # ✅ From CSV (SAJU_LITE_REFINED)
            "algo_version": algo_version,  # ✅ From CSV (v1.5.10+astro)
            "delta_t_range_seconds": delta_t_range,  # ✅ Shows variation
            "entry_count": len(entries)  # ✅ Useful context
        },
    )
    
    return TermResponse(...)
```

---

## 4. Implementation Steps

### Step 1: Modify `get_terms()` Method
**File:** `services/astro-service/app/core/service.py`

**Changes:**
1. After loading entries (line 28), calculate statistics
2. Replace hardcoded TraceMetadata values with computed ones
3. Add proper handling for empty entries list

### Step 2: Update Tests (if exist)
- Verify trace contains computed delta_t
- Check that tzdbVersion uses service parameter
- Validate astro field structure

### Step 3: Verify with Real Data
```bash
cd services/astro-service
env PYTHONPATH=".:../.." ../../.venv/bin/python -c "
from app.core.service import SolarTermService
from app.core.loader import SolarTermLoader
from app.models import TermQuery
from pathlib import Path

loader = SolarTermLoader(table_path=Path('../../data'))
service = SolarTermService(loader=loader, tzdb_version='2025a')

query = TermQuery(year=2000, timezone='Asia/Seoul')
response = service.get_terms(query)

print(f'Delta_t in trace: {response.trace[\"deltaTSeconds\"]}')
print(f'TzdbVersion: {response.trace[\"tz\"][\"tzdbVersion\"]}')
print(f'Astro primary: {response.trace[\"astro\"][\"primary\"]}')
print(f'Delta_t range: {response.trace[\"astro\"][\"delta_t_range_seconds\"]}')
"
```

---

## 5. Expected Before/After

### Before (Hardcoded)
```json
{
  "trace": {
    "rule_id": "KR_classic_v1.4",
    "deltaTSeconds": 57.4,
    "tz": {
      "iana": "Asia/Seoul",
      "event": "none",
      "tzdbVersion": "2025a"
    },
    "astro": {
      "primary": "AstronomyEngine",
      "diffSeconds": 0.0
    }
  }
}
```

### After (Computed)
```json
{
  "trace": {
    "rule_id": "KR_classic_v1.4",
    "deltaTSeconds": 63.08,
    "tz": {
      "iana": "Asia/Seoul",
      "event": "none",
      "tzdbVersion": "2025a"
    },
    "astro": {
      "primary": "SAJU_LITE_REFINED",
      "algo_version": "v1.5.10+astro",
      "delta_t_range_seconds": 0.30,
      "entry_count": 12
    }
  }
}
```

**Key Changes:**
- `deltaTSeconds`: 57.4 → 63.08 (actual average)
- `tzdbVersion`: uses service parameter (already correct in this example)
- `astro.primary`: "AstronomyEngine" → "SAJU_LITE_REFINED"
- `astro`: Added `algo_version`, `delta_t_range_seconds`, `entry_count`
- Removed: `diffSeconds` (replaced with more informative fields)

---

## 6. Edge Cases

### Case 1: Empty Entries
**Scenario:** No solar terms found for year (e.g., invalid year)  
**Handling:** Use default values (delta_t=0.0, source="unknown")

### Case 2: Single Entry
**Scenario:** Only one term in results  
**Handling:** Range will be 0.0, avg is that single value

### Case 3: Different Sources/Versions
**Scenario:** Entries have different sources (unlikely but possible)  
**Handling:** Use first entry's source and add note in algo_version if needed

---

## 7. Testing Strategy

### Unit Tests
1. Test with normal year (2000) - should return computed values
2. Test with empty entries - should return defaults
3. Test with single entry - should handle gracefully

### Integration Tests
1. Verify trace structure matches TraceMetadata schema
2. Check delta_t is within reasonable range (50-70s for modern times)
3. Verify tzdbVersion matches service initialization

### Manual Verification
```bash
# Test for year 2000
python -c "from app.core.service import SolarTermService; ..."

# Test for year 1900 (older delta_t)
python -c "from app.core.service import SolarTermService; ..."

# Compare delta_t values
echo "Expected: ~63s for 2000, ~0s for 1900"
```

---

## 8. Risk Assessment

### Risk Level: LOW ✅

**Why Low Risk:**
1. **Simple computation** - just averaging values
2. **No logic changes** - only trace metadata affected
3. **No breaking changes** - trace is metadata only
4. **Easy to verify** - can check with real data
5. **Easy to rollback** - single file change

### Potential Issues
- **None identified** - This is straightforward metadata fix

---

## 9. Dependencies

### No External Dependencies
- Uses existing TermEntry structure
- Uses existing TraceMetadata class
- No new imports needed

### No Blocking Tasks
- Can be implemented immediately
- Does not depend on other tasks

---

## 10. Success Criteria

✅ **Verification Checklist:**
1. [ ] delta_t_seconds uses computed average (not 57.4)
2. [ ] tzdbVersion uses service parameter (not hardcoded)
3. [ ] astro.primary uses CSV source (not "AstronomyEngine")
4. [ ] astro includes algo_version from CSV
5. [ ] astro includes delta_t_range_seconds showing variation
6. [ ] astro includes entry_count for context
7. [ ] Empty entries handled gracefully
8. [ ] Service import test passes
9. [ ] get_terms() returns valid response
10. [ ] Trace structure validates correctly

---

## 11. Implementation Code

### Complete Fixed Code

```python
def get_terms(self, query: TermQuery) -> TermResponse:
    """Get solar terms for a year with computed trace metadata."""
    tz = ZoneInfo(query.timezone)
    entries = [_with_timezone(entry, tz) for entry in self._loader.load_year(query.year)]
    
    # Calculate statistics from loaded entries
    if entries:
        delta_t_values = [e.delta_t_seconds for e in entries]
        avg_delta_t = sum(delta_t_values) / len(delta_t_values)
        delta_t_range = max(delta_t_values) - min(delta_t_values) if len(delta_t_values) > 1 else 0.0
        source = entries[0].source
        algo_version = entries[0].algo_version
    else:
        # Fallback for empty results (shouldn't happen with valid years)
        avg_delta_t = 0.0
        delta_t_range = 0.0
        source = "unknown"
        algo_version = "unknown"
    
    trace = TraceMetadata(
        rule_id="KR_classic_v1.4",
        delta_t_seconds=avg_delta_t,
        tz={"iana": query.timezone, "event": "none", "tzdbVersion": self._tzdb_version},
        astro={
            "primary": source,
            "algo_version": algo_version,
            "delta_t_range_seconds": delta_t_range,
            "entry_count": len(entries),
        },
    )
    
    return TermResponse(
        year=query.year,
        timezone=query.timezone,
        terms=entries,
        trace=trace.to_dict(),
    )
```

---

## 12. Timeline

**Estimated:** 1-2 hours total

- **Analysis:** 15 minutes ✅ (complete)
- **Planning:** 30 minutes ✅ (this document)
- **Implementation:** 15 minutes
- **Testing:** 15 minutes
- **Documentation:** 15 minutes
- **Buffer:** 30 minutes

---

## 13. Next Steps

1. **Review this plan** - Confirm approach is acceptable
2. **Implement fix** - Modify service.py as outlined
3. **Test thoroughly** - Verify with multiple years
4. **Document changes** - Update any relevant docs
5. **Commit** - Single atomic commit for this fix

---

**Plan Created:** 2025-10-11  
**Task Priority:** HIGH  
**Ready for Implementation:** ✅ YES  
**Estimated Completion:** 15-30 minutes from approval
