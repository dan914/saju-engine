# Stage 2 — Gaps & Risks

## HIGH Priority

- [ ] **LLM Guard v1.1 Integration**
  - Risk: v1.1 policy signed but runtime integration pending
  - Impact: Cannot enforce cross-engine consistency rules
  - Owner: Backend team
  - ETA: T+3d

- [ ] **engine_summaries Pipeline**
  - Risk: engine_summaries injection point not confirmed
  - Impact: CONSIST-450, REL-OVERWEIGHT-410, YONGSHIN-UNSUPPORTED-460 cannot trigger
  - Owner: Analysis service team
  - ETA: T+5d

## MEDIUM Priority

- [ ] **Relation Weight conditions_met Propagation**
  - Risk: conditions_met[] may not flow from Relation Weight to Guard input
  - Impact: REL-OVERWEIGHT-410 may have false negatives
  - Owner: Relation engine team
  - ETA: T+7d

- [ ] **Test Coverage Gaps**
  - Risk: Some v1.1 rules lack edge case coverage
  - Impact: Reduced confidence in production behavior
  - Owner: QA team
  - ETA: T+10d

## LOW Priority

- [ ] **Documentation Sync**
  - Risk: Some handover docs reference old signatures
  - Impact: Developer confusion
  - Owner: Tech writers
  - ETA: T+14d

- [ ] **CI Audit Hooks**
  - Risk: No automated audit on policy changes
  - Impact: Manual verification required
  - Owner: DevOps team
  - ETA: T+14d

---

## Acceptance Criteria

### HIGH Priority
- [ ] All v1.1 rules trigger correctly in E2E test
- [ ] engine_summaries present in all Guard invocations
- [ ] Cross-engine consistency validated with 3 sample sets

### MEDIUM Priority
- [ ] conditions_met[] verified in 10 relation scenarios
- [ ] Test coverage ≥ 2 cases per v1.1 rule
- [ ] Regression test suite passes

### LOW Priority
- [ ] All handover docs updated
- [ ] CI workflow runs on PR
- [ ] Audit reports auto-generated
