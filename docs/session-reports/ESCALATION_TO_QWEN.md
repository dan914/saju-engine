# Escalation Summary: 子時 (Zi Hour) + LMT Logic Discrepancy

**Date:** 2025-10-03
**Issue:** One test case fails due to inconsistent handling of midnight boundary with LMT
**Status:** Need expert guidance on correct Korean Saju tradition

---

## The Problem

### Test Case: 2021-01-01 00:01 (Asia/Seoul)

**Our Engine Output:**
- Year/Month: 庚子 戊子 ✅
- Day/Hour: **戊申 壬子** ❌

**Reference Expected:**
- Year/Month: 庚子 戊子 ✅
- Day/Hour: **己酉 甲子** ✅

**Result:** Day and Hour pillars don't match

---

## Root Cause Analysis

### What Happens in Our Engine

**Input:** 2021-01-01 00:01 (user's clock time)

**Step 1: Save original hour BEFORE adjustments**
```python
original_hour = 0  # User said "00:01"
```

**Step 2: Apply DST (none for this date)**
```python
# No DST in 2021
```

**Step 3: Apply LMT (Seoul -32 minutes)**
```python
2021-01-01 00:01 → 2020-12-31 23:29 (LMT adjusted)
```

**Step 4: Check 子時 (Zi hour) rule**
```python
if original_hour == 23:  # Check ORIGINAL hour (before LMT)
    # 야자시 (Night Zi): Use next day
    zi_transition_applied = True
    day_for_pillar = lmt_adjusted.date() + 1
else:
    # 조자시 (Morning Zi) or other hours: Use current day
    zi_transition_applied = False
    day_for_pillar = lmt_adjusted.date()  # 2020-12-31
```

**Result:**
- `original_hour = 0` (not 23)
- `zi_transition_applied = False`
- `day_for_pillar = 2020-12-31` (LMT-adjusted date)
- Day pillar: 戊申 (based on Dec 31, 2020)
- Hour pillar: 壬子 (based on 戊 day stem)

---

## The Philosophical Inconsistency

### Our Current Hybrid Approach:

1. **子時 check:** Based on **user's clock time** (original_hour)
   - Reasoning: "The user perceives 00:01 as 조자시 of Jan 1"

2. **Day pillar calculation:** Based on **astronomical time** (LMT-adjusted)
   - Reasoning: "Astronomical accuracy requires LMT"

**This creates a mismatch:**
- User says: "I was born 2021-01-01 00:01" (조자시)
- LMT says: Astronomical time was 2020-12-31 23:29 (should be 야자시?)
- We check zi using user time (0:01 = no zi rule)
- But calculate day using astronomical time (Dec 31)

**Result:** Neither fully user-time nor fully astronomical-time

---

## Two Proposed Solutions

### Solution A: Full Astronomical Approach (ChatGPT's suggestion)

**Check 子時 AFTER LMT adjustment:**

```python
# Step 1: Apply LMT first
lmt_adjusted = birth_dt - timedelta(minutes=32)
# 2021-01-01 00:01 → 2020-12-31 23:29

# Step 2: Check zi hour on LMT-adjusted time
if lmt_adjusted.hour == 23:  # Check AFTER LMT
    # 야자시: Use next day
    zi_transition_applied = True
    day_for_pillar = lmt_adjusted.date() + 1  # 2021-01-01
else:
    zi_transition_applied = False
    day_for_pillar = lmt_adjusted.date()
```

**Result for 2021-01-01 00:01:**
- LMT: 2020-12-31 23:29
- Hour is 23 → 야자시 rule applies
- Day: 2021-01-01 (next day from LMT)
- **Day pillar: 己酉 ✅ MATCHES REFERENCE**
- **Hour pillar: 甲子 ✅ MATCHES REFERENCE**

**Pros:**
- ✅ Philosophically consistent (all astronomical)
- ✅ Matches reference output
- ✅ Matches FortuneTeller (validated H01/H02)
- ✅ Professional Saju software likely uses this

**Cons:**
- ❓ Is this how Korean Saju tradition actually works?

---

### Solution B: Full User-Perceived Approach

**Don't use LMT for day pillar at all:**

```python
# Check zi hour on user's clock time
if original_hour == 23:
    day_for_pillar = birth_dt.date() + 1  # Original date + 1
else:
    day_for_pillar = birth_dt.date()  # Original date

# Don't use LMT-adjusted date
```

**Result for 2021-01-01 00:01:**
- Original hour: 0 → 조자시 (no zi rule)
- Day: 2021-01-01 (original date)
- **Day pillar: 己酉 ✅ MATCHES REFERENCE**
- **Hour pillar: 甲子 ✅ MATCHES REFERENCE**

**Pros:**
- ✅ User-friendly (matches user's perception)
- ✅ Matches reference output
- ✅ Simpler logic

**Cons:**
- ❌ Loses astronomical accuracy
- ❌ Inconsistent with LMT usage elsewhere

---

## Current Implementation Details

**File:** `scripts/calculate_pillars_traditional.py`

**Lines 147-217:** The zi hour logic

```python
# Line 148: Save original hour BEFORE DST/LMT
original_hour = birth_dt.hour

# Line 150-176: Apply DST if applicable
# (modifies birth_dt but original_hour already saved)

# Line 183: Apply LMT
lmt_adjusted = birth_dt - timedelta(minutes=abs(lmt_offset_minutes))

# Line 191-201: Check zi hour using ORIGINAL hour
if zi_hour_mode == 'traditional':
    if original_hour == 23:  # ← Checks user's clock time
        day_for_pillar = lmt_adjusted.date() + timedelta(days=1)
        zi_transition_applied = True
    else:
        day_for_pillar = lmt_adjusted.date()  # ← Uses astronomical date
```

**The inconsistency:** We check zi using user time but calculate day using astronomical time.

---

## Why This Matters

### Current Test Results:

**10 Reference Cases:** 38/40 pillars (95%)
- ✅ 9 cases: 100% match
- ❌ 1 case (2021-01-01 00:01): Day + Hour wrong

**30 Mixed Cases:** 27/30 tests (90%)
- Same case passes in 30-test suite because reference values are different
- Different source or different calculation method

**DST Cases (H01/H02):** 2/2 (100%)
- These validated against FortuneTeller
- FortuneTeller uses LMT + astronomical approach

---

## The Question for Traditional Experts

**In traditional Korean Saju practice:**

**When determining 야자시/조자시 (Night Zi vs Morning Zi):**

1. **Do you check the hour BEFORE or AFTER Local Mean Time adjustment?**

2. **If someone is born at clock time 00:01:**
   - After LMT (-32 min), astronomical time is 23:29 previous day
   - Is this considered:
     - **야자시** (Night Zi of current day) because astronomical hour is 23?
     - **조자시** (Morning Zi of current day) because clock shows 00?

3. **What do traditional texts say?**
   - Is 子時 rule based on "apparent solar time" (astronomical)?
   - Or based on "civil clock time" (what people see)?

---

## Test Case Behavior Matrix

| Input | Original Hour | LMT Hour | Current Logic | Solution A | Solution B | Reference |
|-------|--------------|----------|---------------|------------|------------|-----------|
| 2021-01-01 00:01 | 0 | 23 | 戊申 壬子 | 己酉 甲子 ✅ | 己酉 甲子 ✅ | 己酉 甲子 |
| 2021-01-01 23:30 | 23 | 22 | 丙子 己亥 | 乙亥 丁亥 | 丙子 己亥 | ? |
| 2020-12-31 23:59 | 23 | 23 | 己酉 甲子 | 己酉 甲子 | 己酉 甲子 | 己酉 甲子 |

**Note:** Only the midnight boundary case (00:0X after LMT becomes 23:XX) shows discrepancy.

---

## Related Documentation

**Our previous implementation decision (2025-10-02):**
- File: `ZI_HOUR_MODE_IMPLEMENTATION.md`
- Decision: "Check 야자시/조자시 using user's perceived clock time"
- Reasoning: "User says 'I was born at 23:30' - that's 子時 to them"

**But this creates inconsistency when combined with LMT for day calculations.**

---

## What We Need from Qwen

1. **Historical/Traditional Guidance:**
   - What do traditional Korean Saju texts say?
   - Is 子時 based on apparent solar time or civil time?
   - How do professional Korean Saju practitioners handle this?

2. **Recommendation:**
   - Should we use Solution A (full astronomical)?
   - Should we use Solution B (full user-perceived)?
   - Or keep current hybrid (with known edge case)?

3. **Validation:**
   - Can you check how other Korean Saju software (만세력, 토정비결, etc.) handles 2021-01-01 00:01?
   - What day/hour pillars do they produce?

---

## Impact Assessment

**If we change to Solution A (check zi after LMT):**
- ✅ Fixes 2021-01-01 00:01 case
- ✅ More consistent with FortuneTeller
- ✅ Philosophically coherent
- ⚠️ May affect other midnight boundary cases (need regression testing)
- ⚠️ Changes behavior of existing 야자시/조자시 toggle

**If we change to Solution B (no LMT for day pillar):**
- ✅ Fixes 2021-01-01 00:01 case
- ✅ User-friendly
- ❌ Loses astronomical accuracy for other calculations
- ❌ Inconsistent with H01/H02 validation (DST cases)

**If we keep current (hybrid):**
- ⚠️ 1 test case remains wrong (95% vs 100%)
- ⚠️ Philosophically inconsistent
- ✅ No regression risk
- ✅ Can document as "known limitation"

---

## Files to Review

1. `scripts/calculate_pillars_traditional.py` (lines 147-217)
2. `ZI_HOUR_MODE_IMPLEMENTATION.md` (design decision)
3. `scripts/debug_2021_0101.py` (diagnostic script)
4. `REALITY_CHECK_REPORT.md` (overall status)

---

## Request

Please provide guidance on:
1. Traditional Korean Saju practice for 子時 determination
2. Which solution aligns with authentic Korean tradition
3. Any additional test cases we should consider
4. Reference to traditional texts if available

---

**Prepared by:** Claude Code (Sonnet 4.5)
**Date:** 2025-10-03
**Status:** Awaiting expert guidance
