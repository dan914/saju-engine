# Policy Assets Consolidation Plan

**Created:** 2025-11-06
**Status:** Planning Phase
**Related Issue:** Week 4 Task 6 - Consolidate policy assets

## Executive Summary

Currently, policy files are scattered across 11 different directories, creating maintenance complexity and confusion. This plan outlines a strategy to consolidate policy assets into a single canonical location while maintaining backward compatibility.

## Current State Analysis

### Policy Directory Inventory

```
1. policy/                                           (19 files) ✅ CANONICAL
2. saju_codex_batch_all_v2_6_signed/policies/       (30+ files) ⭐ PRIMARY LEGACY
3. saju_codex_addendum_v2/policies/                 (6 files)
4. saju_codex_addendum_v2_1/policies/               (7 files)
5. saju_codex_addendum_v2_3/policies/               (unknown)
6. saju_codex_blueprint_v2_6_SIGNED/policies/       (unknown)
7. saju_codex_full_v2_4/policies/                   (unknown)
8. saju_codex_q4_to_q10/Q4_five_he/policies/        (unknown)
9. saju_codex_q4_to_q10/Q5_deltaT/policies/         (unknown)
10. saju_codex_q4_to_q10/Q8_telemetry/policies/     (unknown)
11. saju_codex_v2_5_bundle/policies/                (unknown)
```

### Settings Configuration (services/common/saju_common/settings.py)

**Current `policy_dirs` priority order:**
```python
policy_dirs: List[str] = Field(
    default=[
        "policy",                                    # 1st priority (CANONICAL)
        "saju_codex_batch_all_v2_6_signed/policies", # 2nd priority
        "saju_codex_addendum_v2/policies",           # 3rd priority
        "saju_codex_addendum_v2_1/policies",         # 4th priority
        "saju_codex_blueprint_v2_6_SIGNED/policies", # 5th priority
        "saju_codex_v2_5_bundle/policies",           # 6th priority
    ]
)
```

**Missing from settings:**
- `saju_codex_addendum_v2_3/policies/`
- `saju_codex_full_v2_4/policies/`
- `saju_codex_q4_to_q10/Q4_five_he/policies/`
- `saju_codex_q4_to_q10/Q5_deltaT/policies/`
- `saju_codex_q4_to_q10/Q8_telemetry/policies/`

### Key Policy Files in Use

**From test_settings.py and actual usage:**
1. `strength_policy_v2.json` - ✅ Found in saju_codex_batch_all_v2_6_signed/
2. `relation_policy.json` - ✅ Found in saju_codex_batch_all_v2_6_signed/ and policy/
3. `shensha_v2_policy.json` - ✅ Found in saju_codex_batch_all_v2_6_signed/
4. `climate_map_v1.json` - ✅ Found in saju_codex_addendum_v2/
5. `localization_ko_v1.json` - ✅ Found in saju_codex_batch_all_v2_6_signed/
6. `sixty_jiazi.json` - ✅ Found in saju_codex_batch_all_v2_6_signed/
7. `gyeokguk_policy.json` - ✅ Found in saju_codex_batch_all_v2_6_signed/ and policy/

**From analysis-service code inspection:**
- `climate_advice_policy_v1.json` - In policy/
- `luck_flow_policy_v1.json` - In policy/
- `pattern_profiler_policy_v1.json` - In policy/
- `gyeokguk_policy_v1.json` - In policy/
- `relation_weight_policy_v1.0.json` - In policy/
- `yongshin_selector_policy_v1.json` - In policy/
- `recommendation_policy_v1.json` - In saju_codex_addendum_v2_1/
- `relation_transform_rules_v1_1.json` - In saju_codex_addendum_v2_1/

## Consolidation Strategy

### Phase 1: Audit & Documentation (Current Phase)

**Objectives:**
1. ✅ Identify all policy directories
2. ✅ Check current settings configuration
3. ⏳ Catalog all policy files with their locations
4. ⏳ Identify actively used vs. orphaned files
5. ⏳ Detect duplicates and version conflicts

**Action Items:**
- [ ] Create comprehensive inventory of all policy files
- [ ] Check each file for usage in codebase (grep analysis)
- [ ] Identify duplicate files (compare by content hash)
- [ ] Document version history and dependencies

### Phase 2: Migration Planning

**Decision Matrix:**

| Category | Strategy | Rationale |
|----------|----------|-----------|
| **Active Core Policies** | Move to `policy/` | Single source of truth |
| **Version Variants** | Keep latest in `policy/` | Reduce version sprawl |
| **Duplicate Files** | Consolidate to `policy/` | Eliminate redundancy |
| **Orphaned Files** | Archive or delete | Reduce clutter |
| **Legacy Directories** | Mark as deprecated | Phase out gradually |

**Target Structure:**
```
policy/
├── core/                  # Core engine policies
│   ├── strength_policy_v2.json
│   ├── relation_policy.json
│   ├── shensha_v2_policy.json
│   └── ...
├── analysis/              # Analysis-specific policies
│   ├── climate_map_v1.json
│   ├── climate_advice_policy_v1.json
│   ├── luck_flow_policy_v1.json
│   └── ...
├── localization/          # Localization files
│   ├── localization_ko_v1.json
│   ├── localization_en_v1.json
│   └── ...
├── reference/             # Reference data
│   ├── sixty_jiazi.json
│   ├── lifecycle_stages.json
│   └── ...
└── llm/                   # LLM-related policies
    ├── llm_guard_policy_v1.json
    ├── llm_guard_policy_v1.1.json
    └── ...
```

### Phase 3: Implementation

**Steps:**
1. **Backup:** Create backup of all policy directories
2. **Copy:** Copy all active files to `policy/` with organized structure
3. **Update:** Update settings.py to search new subdirectories
4. **Test:** Run comprehensive tests to ensure resolution works
5. **Validate:** Verify all services can load policies correctly
6. **Document:** Update documentation with new structure

**Updated settings.py:**
```python
policy_dirs: List[str] = Field(
    default=[
        "policy/core",
        "policy/analysis",
        "policy/localization",
        "policy/reference",
        "policy/llm",
        "policy",  # Root fallback
        # Legacy directories (deprecated, will be removed in future)
        "saju_codex_batch_all_v2_6_signed/policies",
        "saju_codex_addendum_v2/policies",
        "saju_codex_addendum_v2_1/policies",
    ]
)
```

### Phase 4: Deprecation

**Timeline:**
- **Week 4:** Complete consolidation
- **Week 5:** Update all code references
- **Week 6:** Mark legacy directories as deprecated (add DEPRECATED.md)
- **Week 8:** Remove legacy directories from settings
- **Week 10:** Archive legacy directories (move to `archive/`)

## Risk Mitigation

### Risks

1. **Breaking Changes:** Policy resolution may break for some services
   - **Mitigation:** Maintain backward compatibility during transition
   - **Fallback:** Keep legacy directories in search path temporarily

2. **Version Conflicts:** Multiple versions of same policy file
   - **Mitigation:** Careful analysis and testing before consolidation
   - **Strategy:** Keep only latest stable version, archive others

3. **Missing Dependencies:** Some code may hardcode policy paths
   - **Mitigation:** Comprehensive grep analysis before changes
   - **Testing:** Run all tests after migration

4. **Test Failures:** Tests may fail after path changes
   - **Mitigation:** Update tests incrementally
   - **Validation:** Run test suite after each change

### Rollback Plan

1. Keep backup of all policy directories
2. Git commit after each phase
3. Revert settings.py changes if tests fail
4. Restore original directory structure if needed

## Success Criteria

- [ ] All policy files consolidated into `policy/` directory
- [ ] Settings.py updated with new search paths
- [ ] All tests passing (common: 21/21, analysis-service: 631+/657)
- [ ] No duplicate policy files
- [ ] Clear directory structure with logical organization
- [ ] Documentation updated with new structure
- [ ] Legacy directories marked as deprecated

## Next Actions

**Immediate (Phase 1 completion):**
1. Create comprehensive inventory script
2. Identify all actively used policy files
3. Detect duplicates by content hash
4. Document findings in spreadsheet or JSON

**Short-term (Phase 2):**
1. Design final directory structure
2. Plan migration sequence
3. Update settings.py draft
4. Review with team

**Medium-term (Phase 3-4):**
1. Execute migration
2. Update all references
3. Run comprehensive tests
4. Begin deprecation process

## Notes

- **Backward Compatibility:** Critical during transition period
- **Testing:** Must maintain 100% test coverage during migration
- **Documentation:** Update CLAUDE.md after consolidation
- **Git Strategy:** Use feature branch, merge after validation

---

**Status:** Planning phase complete, ready for Phase 1 execution
**Owner:** Backend team
**Review Date:** End of Week 4
