# Midnight Transition Implementation Proposal

**Date:** 2025-10-02
**Issue:** 4 test failures at midnight boundaries (Tests #8, #9)
**Solution:** Implement 23:00 day transition rule (子時 rule)

---

## Problem Statement

Current engine uses 00:00 (midnight) for day transition, but reference data shows:
- Test #8 (23:58): Treats as **next day** (丁丑 not 丙子)
- Test #9 (00:01): Treats as **input day** (己酉 not 戊申)

Both failures occur when 子時 (23:00-01:00) spans two calendar days.

---

## Proposed Solution: Traditional 子時 Rule

### Calculation Order:
1. **Apply LMT adjustment** (-32 min for Seoul)
2. **Apply 子時 transition rule** (23:00 = next day)
3. **Calculate pillars** using adjusted time/date

### Rule Definition:

**For Day & Hour Pillars:**
- If adjusted hour ∈ [23:00, 23:59]: Use **next calendar day**
- Else: Use **same calendar day**

**For Year & Month Pillars:**
- Always use **solar term** at precise astronomical time (with ΔT)
- Unaffected by 子時 rule

---

## Implementation

### Core Function:

```python
def apply_traditional_day_transition(birth_dt: datetime, lmt_offset_minutes: int) -> dict:
    """
    Apply LMT and traditional 子時 day transition rule.

    Args:
        birth_dt: Birth datetime in local timezone
        lmt_offset_minutes: LMT offset (negative for Seoul = -32)

    Returns:
        {
            'for_year_month': datetime,  # For solar term lookup
            'for_day_hour': date         # For day/hour pillar
        }
    """
    # Step 1: Apply LMT
    lmt_adjusted = birth_dt - timedelta(minutes=abs(lmt_offset_minutes))

    # Step 2: Determine day for pillars based on 子時 rule
    if lmt_adjusted.hour == 23:
        # 子時 early period (23:00-23:59) belongs to NEXT day
        day_for_pillars = lmt_adjusted.date() + timedelta(days=1)
    else:
        # All other hours use same day
        day_for_pillars = lmt_adjusted.date()

    return {
        'for_year_month': lmt_adjusted,  # Use full datetime for solar term
        'for_day_hour': day_for_pillars   # Use adjusted date for day/hour
    }
```

### Updated Day Pillar Calculation:

```python
def calculate_day_pillar(adjusted_date: date) -> str:
    """
    Calculate day pillar using adjusted date from 子時 rule.

    Args:
        adjusted_date: Date after LMT and 子時 adjustments
    """
    anchor_date = datetime(1900, 1, 1).date()  # 甲戌
    anchor_index = SEXAGENARY_CYCLE.index('甲戌')  # 10

    delta_days = (adjusted_date - anchor_date).days
    day_index = (anchor_index + delta_days) % 60

    return SEXAGENARY_CYCLE[day_index]
```

### Updated Hour Pillar Calculation:

```python
def calculate_hour_pillar(lmt_adjusted_time: datetime, day_stem: str) -> str:
    """
    Calculate hour pillar using LMT-adjusted time.

    Note: Hour boundaries are fixed 2-hour blocks regardless of day transition.
    子時 = 23:00-00:59, 丑時 = 01:00-02:59, etc.

    Args:
        lmt_adjusted_time: Time after LMT adjustment
        day_stem: Stem from day pillar (already adjusted by 子時 rule)
    """
    hour = lmt_adjusted_time.hour

    # Standard 2-hour boundaries
    hour_branch_index = ((hour + 1) // 2) % 12
    hour_branch = EARTHLY_BRANCHES[hour_branch_index]

    # Calculate stem from day stem
    hour_start_stem = DAY_STEM_TO_HOUR_START[day_stem]
    hour_stem_index = (HEAVENLY_STEMS.index(hour_start_stem) + hour_branch_index) % 10
    hour_stem = HEAVENLY_STEMS[hour_stem_index]

    return hour_stem + hour_branch
```

---

## Expected Results

### Test #8: 2019-08-07 23:58 KST

**Before (Current):**
```
Input:          2019-08-07 23:58 KST
LMT adjusted:   2019-08-07 23:26
Day for pillar: 2019-08-07 (wrong)
Day pillar:     丙子 ❌
Hour pillar:    戊子 ❌
```

**After (Proposed):**
```
Input:          2019-08-07 23:58 KST
LMT adjusted:   2019-08-07 23:26
Hour = 23 → Next day rule applies
Day for pillar: 2019-08-08 ✅
Day pillar:     丁丑 ✅ (matches reference)
Hour pillar:    庚子 ✅ (matches reference)
```

### Test #9: 2021-01-01 00:01 KST

**Before (Current):**
```
Input:          2021-01-01 00:01 KST
LMT adjusted:   2020-12-31 23:29
Day for pillar: 2020-12-31 (wrong - LMT changed date)
Day pillar:     戊申 ❌
Hour pillar:    壬子 ❌
```

**After (Proposed):**
```
Input:          2021-01-01 00:01 KST
LMT adjusted:   2020-12-31 23:29
Hour = 23 → Next day rule applies
Day for pillar: 2021-01-01 ✅ (matches input!)
Day pillar:     己酉 ✅ (matches reference)
Hour pillar:    甲子 ✅ (matches reference)
```

**Key Insight:** Test #9 shows the elegance of this rule - when LMT pushes time to 23:xx, the 子時 rule automatically bumps it back to the input day!

---

## Calculation Mode System

### Mode Definitions:

```python
CALCULATION_MODES = {
    'traditional_kr': {
        'name': 'Traditional Korean (FortuneTeller compatible)',
        'use_lmt': True,
        'lmt_offset_seoul': -32,  # minutes
        'day_transition_hour': 23,  # 子時 rule
        'solar_terms': 'refined',   # Astronomical precision with ΔT
        'description': 'Matches traditional Korean Saju apps'
    },

    'modern': {
        'name': 'Modern Astronomical',
        'use_lmt': False,
        'day_transition_hour': 0,  # Midnight
        'solar_terms': 'refined',
        'description': 'Uses standard timezone and midnight transition'
    },

    'hybrid': {
        'name': 'Hybrid (LMT for solar terms only)',
        'use_lmt': True,
        'lmt_offset_seoul': -32,
        'day_transition_hour': 0,  # Midnight
        'solar_terms': 'refined',
        'description': 'LMT for year/month, modern for day/hour'
    }
}
```

### API Interface:

```python
def calculate_four_pillars(
    birth_datetime: datetime,
    timezone: str = 'Asia/Seoul',
    mode: str = 'traditional_kr',
    lmt_offset_minutes: Optional[int] = None,
    return_metadata: bool = False
) -> dict:
    """
    Calculate Four Pillars with configurable calculation mode.

    Args:
        birth_datetime: Birth time in specified timezone
        timezone: IANA timezone (e.g., 'Asia/Seoul')
        mode: Calculation mode ('traditional_kr', 'modern', 'hybrid')
        lmt_offset_minutes: Manual LMT override (None = auto-calculate)
        return_metadata: Include calculation details in result

    Returns:
        {
            'year': '庚子',
            'month': '戊子',
            'day': '己酉',
            'hour': '甲子',
            'metadata': {  # if return_metadata=True
                'mode': 'traditional_kr',
                'lmt_offset': -32,
                'lmt_adjusted_time': '2020-12-31 23:29',
                'day_transition_applied': True,
                'solar_term': '大雪',
                'solar_term_time': '2020-12-06 18:09:21',
                'data_source': 'SAJU_LITE_REFINED',
                'algo_version': 'v1.5.10+astro+zi_rule'
            }
        }
    """
    # Implementation here
    pass
```

---

## Migration Plan

### Phase 1: Implementation (Week 1)
- [ ] Add `apply_traditional_day_transition()` function
- [ ] Update `calculate_day_pillar()` to accept adjusted date
- [ ] Update `calculate_hour_pillar()` with correct day stem
- [ ] Add mode configuration system
- [ ] Add LMT offset table for major cities

### Phase 2: Testing (Week 1-2)
- [ ] Run existing 10 test cases with new rule
- [ ] Verify 40/40 (100%) accuracy target
- [ ] Create 48 midnight boundary test cases
- [ ] Create 36 solar term boundary test cases
- [ ] Achieve ≥95% on expanded suite (100+ cases)

### Phase 3: Validation (Week 2)
- [ ] Cross-validate with FortuneTeller app (20+ cases)
- [ ] Test multiple cities (Seoul, Busan, Gwangju, etc.)
- [ ] Document any remaining edge cases
- [ ] Get user feedback on traditional vs modern modes

### Phase 4: Deployment (Week 3)
- [ ] Update DATA_SOURCES.md with 子時 rule explanation
- [ ] Add mode selection to API/CLI
- [ ] Default to 'traditional_kr' for Korean users
- [ ] Add migration guide for existing users
- [ ] Deploy to production

---

## Testing Strategy

### Midnight Boundary Tests (48 cases)

For each of 3 dates (regular, solar term ±1):
- 23:00, 23:15, 23:30, 23:45 (should use next day)
- 00:00, 00:15, 00:30, 00:45 (should use same day)

Expected pattern:
```
23:00 → Next day ✅
23:15 → Next day ✅
23:30 → Next day ✅
23:45 → Next day ✅
00:00 → Same day ✅
00:15 → Same day ✅
00:30 → Same day ✅
00:45 → Same day ✅
```

### Validation Script:

```python
def test_midnight_transitions():
    """Test 子時 transition rule."""
    test_cases = [
        # (input_time, expected_day_offset, expected_hour_branch)
        ("23:00", +1, "子"),  # Early 子時 → next day
        ("23:30", +1, "子"),
        ("23:59", +1, "子"),
        ("00:00", 0, "子"),   # Late 子時 → same day
        ("00:30", 0, "子"),
        ("00:59", 0, "子"),
        ("01:00", 0, "丑"),   # Normal hours
        ("12:00", 0, "午"),
    ]

    for time_str, day_offset, hour_branch in test_cases:
        birth_dt = datetime.strptime(f"2025-01-15 {time_str}", "%Y-%m-%d %H:%M")
        result = calculate_four_pillars(birth_dt, mode='traditional_kr')

        # Verify day transition
        expected_date = birth_dt.date() + timedelta(days=day_offset)
        # ... validation logic
```

---

## Documentation Updates

### DATA_SOURCES.md Addition:

```markdown
## Calculation Rules

### 子時 (Zi Hour) Day Transition Rule

Traditional Korean Saju calculations use the **23:00 day transition rule**:

- **子時 (23:00-00:59)** straddles two calendar days
- **Early 子時 (23:00-23:59)**: Belongs to **next day's** pillars
- **Late 子時 (00:00-00:59)**: Belongs to **same day's** pillars

**Example:**
- Birth: 2019-08-07 23:58 → Day pillar uses 2019-08-08
- Birth: 2019-08-08 00:01 → Day pillar uses 2019-08-08

This matches traditional Chinese timekeeping where each day begins at 子時 (23:00), not midnight (00:00).

**Calculation Order:**
1. Apply Local Mean Time (LMT) adjustment
2. Apply 子時 transition rule (if hour = 23)
3. Calculate day and hour pillars

**Modes:**
- `traditional_kr`: Uses 子時 rule (recommended for Korean Saju)
- `modern`: Uses midnight (00:00) transition
- `hybrid`: LMT for solar terms only, midnight for day/hour
```

---

## Risk Assessment

### Low Risk ✅
- **Well-documented traditional rule** (not a hack)
- **Clear test pattern** (all 4 failures at 23:xx or 00:xx)
- **Reversible** (mode system allows fallback)
- **Improves accuracy** (90% → 100% expected)

### Mitigation:
- Feature flag allows A/B testing
- Metadata logging shows which rule was applied
- User can choose mode based on preference

---

## Success Metrics

### Primary Goal:
- **100% accuracy (40/40)** on FortuneTeller reference data ✅

### Secondary Goals:
- **≥95% accuracy** on expanded test suite (100+ cases)
- **≥98% accuracy** on midnight boundary cases (48 cases)
- **100% accuracy** on solar term boundaries (36 cases)

### Quality Metrics:
- Zero regression on existing passing tests
- Complete documentation of calculation rules
- User-selectable modes working correctly

---

## Timeline

- **Week 1**: Implementation + Initial Testing
- **Week 2**: Expanded Testing + Validation
- **Week 3**: Documentation + Deployment
- **Week 4**: Monitor production + User feedback

**Target Completion:** 2025-10-30

---

## Appendix: Alternative Considered (Rejected)

### Why Not "Conditional LMT"?

ChatGPT correctly identified this as problematic:
- Creates inconsistency between year/month and day/hour
- No traditional basis
- Harder to explain to users
- Doesn't solve Test #8 (which doesn't cross midnight)

### Why Not "23:30 Rounding"?

- Arbitrary cutoff with no historical basis
- Would fail cases at 23:29 vs 23:31
- No other Saju calculator uses this
- Doesn't align with traditional 2-hour 子時 period

### Why 子時 Rule is Superior:

- ✅ Traditional basis (centuries old)
- ✅ Matches reference app behavior
- ✅ Solves both failure patterns
- ✅ Consistent with other BaZi calculators
- ✅ Easy to explain and document

---

**Prepared By:** Saju Engine Development Team
**Reviewed By:** ChatGPT Analysis
**Status:** Approved for Implementation
