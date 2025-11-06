# Strength Engine v2 Alignment Plan

## Purpose
StrengthEvaluator v2 determines the chart’s overall 신강/신약 profile and feeds Yongshin, Structure, and narrative engines. Today the evaluator (`services/analysis-service/app/core/strength_v2.py`) hardcodes weights and only returns numeric scores, leaving schema fields like `level` and `basis` blank. This plan realigns the implementation with the signed policies.

## Key Policies
- `strength_policy_v2.json` (version 2.0.1)
  - Defines the full scoring model: 득령(30%), 득지(25%), 득시(10%), 득세(35%).
  - Encodes month 旺 map, branch rooting affinity, lifecycle (十二운성) usage, balance penalties, and climate adjustments.
  - Provides buckets (`태강/중강/중화/중약/태약`) with multi-locale labels and rounding rules.
- `strength_adjust_v1_3.json`
  - Interim numeric adjustments: seasonal state weights, relation scoring budget, grading hysteresis.
  - Should be merged or superseded by v2 policy to avoid conflicting constants.
- `strength_scale_v1_1.json`
  - Legacy state-point mapping; keep as migration reference but retire once v2 policy is live.
- `lifecycle_stages.json`
  - Supplies 十二운성 mapping (variant=`mirror`) and overlay weights used in 득시 scoring.
- `seasons_wang_map_v2.json`
  - Month branch vs element 旺相休囚死 table used by 득령 and climate modifiers.
- `relation_aggregate_policy_v1.json` & `relation_structure_adjust_v2_5.json`
  - Provide post-structure relation bonuses/penalties referenced in 득세 and final adjustment budget.

## Functional Requirements
1. **Policy Loading**
   - Use `services.common.policy_loader` to load `strength_policy_v2.json` (fail fast if missing or signature mismatch).
   - Inject dependency versions into output metadata for audit; expose `policy_meta` in `StrengthResult`.
2. **Scoring Pipeline**
   - 득령: Evaluate month branch support via policy’s `month_wang_map` and `scoring` thresholds; include polarity guard logic.
   - 득지: Compute rooting via hidden stem weights (`common_hidden_weights`) across all four pillars, respecting `pillar_weights` and affinity table.
   - 득시: Hour support using `branch_primary_element_map`, adjustable weight for hidden stems, and the same affinity logic.
   - 득세: Combine element balance penalties (`balance.vector`, variance/ skew caps) and climate adjustments (`climate_adjust.segments`), ensuring percentages come from the rebuilt Element Engine.
   - Apply relation bonuses only when structure status allows (`relation_scoring.apply_when`).
   - Normalise raw score via policy’s min/max and assign bucket labels.
3. **Schema Output**
   - Populate `StrengthResult` (`services/analysis-service/app/models/analysis.py`) with:
     - `score_raw`, `score_normalized` (0-100), `level` (e.g., `"태약"`), `basis` (KO/EN label summary), `factors` (list of component contributions), `debug` (per-factor traces), and `policy_meta`.
   - Provide `relative_need` (favour/support/control) derived from balance vector to keep Yongshin consistent.
4. **Configurability & Extensibility**
   - Honour `options.relation_policy.apply` flag for relation influence.
   - Support alternate lifecycle variants (mirror vs orthodox) through policy toggle.
   - Permit future climate map revisions (`climate_map_v1.json`) without code changes.

## Integration Tasks
- Encapsulate the new logic in a dedicated module (e.g., `core/strength_engine.py`) to replace legacy `StrengthEvaluator` while preserving interface expected by orchestrator.
- Update orchestrator to pass the richer `StrengthResult` directly to response models; remove ad-hoc conversions in `saju_orchestrator._call_strength`.
- Sync `AnalysisResponse` schema with new fields and ensure Ten Gods/structure/recommendation engines read `level` and `basis`.

## Testing Strategy
- Unit tests per subsystem (득령, 득지, 득시, 득세) using synthetic charts and policy-provided thresholds.
- Regression snapshots for benchmark charts (e.g., `庚辰·乙酉·乙亥·辛巳`, `甲子·戊午·戊申·丙子`) comparing raw + normalized scores against policy-calculated expectations.
- Property-based tests to enforce invariants (`weights sum to 100`, normalized range 0-100, climate adjustments within caps).
- Contract test verifying `StrengthResult` serialises through Pydantic without loss and matches response schema.

## Migration Notes
- Document differences from legacy scoring in `CHANGELOG_strength_engine_v2.md` and provide conversion guidance for analytics dashboards.
- Coordinate with policy owners to lock `strength_policy_v2.json` signature after implementation.
- Update fixtures such as `test_result_2000_09_14_full.json` once new engine is stable.
