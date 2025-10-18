# Stage 2 — Action Plan

## T+0~3d (Immediate)

### 1. Policy Signature Verification ✅
- **Owner:** DevOps
- **Tasks:**
  - [x] Run PSA verify on all policies
  - [ ] Re-sign any UNSIGNED policies
  - [ ] Update handover docs with new hashes
- **Acceptance:** All policies signed and verified

### 2. LLM Guard v1.1 Schema Validation ✅
- **Owner:** Backend
- **Tasks:**
  - [x] Validate v1.1 input/output schemas
  - [ ] Test with sample engine_summaries payload
  - [ ] Document required fields
- **Acceptance:** Schema validation passes with all required fields

## T+4~7d (Short-term)

### 3. engine_summaries Integration
- **Owner:** Analysis Service
- **Tasks:**
  - [ ] Identify injection point in analysis pipeline
  - [ ] Add engine_summaries builder
  - [ ] Unit test summaries construction
- **Acceptance:** engine_summaries present in all Guard calls

### 4. Cross-Engine Consistency E2E
- **Owner:** QA + Backend
- **Tasks:**
  - [ ] Create 3 test sets (신약/중화/신강)
  - [ ] Run E2E with v1.1 Guard
  - [ ] Verify CONSIST-450 triggers correctly
- **Acceptance:** All 3 scenarios produce expected verdicts

### 5. Test Coverage Enhancement
- **Owner:** QA
- **Tasks:**
  - [ ] Add edge cases for v1.1 rules
  - [ ] Validate revise → allow conversion rate
  - [ ] Document test case rationale
- **Acceptance:** ≥2 cases per v1.1 rule, ≥80% revise→allow rate

## T+8~14d (Medium-term)

### 6. Relation Weight conditions_met Propagation
- **Owner:** Relation Engine
- **Tasks:**
  - [ ] Verify conditions_met[] in Relation Weight output
  - [ ] Ensure propagation to Guard input
  - [ ] Test REL-OVERWEIGHT-410 triggering
- **Acceptance:** 10 test scenarios validated

### 7. Performance & Timeout Policies
- **Owner:** Backend
- **Tasks:**
  - [ ] Set Guard timeout ≤1500ms
  - [ ] Implement fallback on timeout
  - [ ] Add retry backoff for model errors
- **Acceptance:** p95 Guard latency <1.5s, 0 timeouts in 1000 calls

### 8. Documentation & Release
- **Owner:** Tech Writers + DevOps
- **Tasks:**
  - [ ] Sync all handover docs
  - [ ] Tag releases (llm-guard-v1.1.0, etc.)
  - [ ] Generate CHANGELOG entries
- **Acceptance:** All docs current, tags pushed

## T+15~21d (Long-term)

### 9. CI/CD Integration
- **Owner:** DevOps
- **Tasks:**
  - [ ] Add stage2_audit.yml to GitHub Actions
  - [ ] Auto-run on policy/** changes
  - [ ] Upload reports as artifacts
- **Acceptance:** CI passes on all PRs

### 10. Monitoring & Alerting
- **Owner:** SRE
- **Tasks:**
  - [ ] Add Guard metrics (verdict distribution, latency)
  - [ ] Set up alerts for high revise rate
  - [ ] Dashboard for rule trigger frequency
- **Acceptance:** Metrics visible in production

---

## Rollback Plan

If critical issues found:
1. Revert to v1.0 Guard (9 rules)
2. Disable cross-engine consistency checks
3. Investigate root cause offline
4. Re-deploy v1.1 after fix
