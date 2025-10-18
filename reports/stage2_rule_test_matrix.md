# LLM Guard Rule ↔ Test Coverage Matrix

**Primary Test Suite:** v1.1 (single source of truth)
**v1.0 Status:** Legacy/regression only (heuristic coverage detection)


## v1.0 (llm_guard_cases_v1.jsonl)

| Rule ID | Coverage | Test Cases |
|---------|----------|------------|
| STRUCT-000 | ⚠️ | **NO COVERAGE** |
| EVID-BIND-100 | ✅ | allow_normal_with_evidence (heuristic), revise_no_evidence (heuristic) |
| SCOPE-200 | ✅ | deny_out_of_scope_medical (heuristic), deny_out_of_scope_birth_time (heuristic), deny_out_of_scope_death (heuristic) |
| MODAL-300 | ✅ | allow_proper_modality (heuristic), revise_modality_overclaim (heuristic) |
| REL-400 | ✅ | allow_relation_match (heuristic), revise_relation_mismatch (heuristic) |
| SIG-500 | ⚠️ | **NO COVERAGE** |
| PII-600 | ✅ | revise_pii_phone (heuristic), deny_severe_pii_ssn (heuristic) |
| KO-700 | ✅ | allow_proper_ko_labels (heuristic), revise_no_ko_labels (heuristic) |
| AMBIG-800 | ✅ | revise_ambiguous_source (heuristic) |

## v1.1 (llm_guard_v1.1_cases.jsonl)

| Rule ID | Coverage | Test Cases |
|---------|----------|------------|
| STRUCT-000 | ✅ | STRUCT-000-001 |
| EVID-BIND-100 | ✅ | EVID-BIND-100-001 |
| SCOPE-200 | ✅ | SCOPE-200-001 |
| MODAL-300 | ✅ | MODAL-300-001 |
| REL-400 | ✅ | REL-400-001 |
| SIG-500 | ✅ | SIG-500-001 |
| PII-600 | ✅ | PII-600-001 |
| KO-700 | ✅ | KO-700-001 |
| AMBIG-800 | ✅ | AMBIG-800-001 |
| CONF-LOW-310 | ✅ | CONF-LOW-310-001 |
| REL-OVERWEIGHT-410 | ✅ | REL-OVERWEIGHT-410-001 |
| CONSIST-450 | ✅ | CONSIST-450-001 |
| YONGSHIN-UNSUPPORTED-460 | ✅ | YONGSHIN-UNSUPPORTED-460-001 |