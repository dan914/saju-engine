# Structure Engine (Gyeokguk) Implementation Spec

## Mission
Deliver 격국 classification consistent with signed policies so that Analysis API responses include primary structure, variants, and confidence. Stage-3 engines already compute candidate scores, but the orchestrator drops them, leaving `AnalysisResponse.structure` empty.

## Policy Stack
- `gyeokguk_policy.json` (v1.0.0)
  - Comprehensive rule set covering core/bonus/penalty/breaker conditions per structure (정관, 칠살, 정재, 편재, 식상, 인성, 비겁, 종격 variants).
  - Defines scoring caps, normalization ((-30 → 30) → 0-100), status thresholds (成格/假格/破格), confidence formula, tie-breakers, and selectors (strength, relation, projection keys).
- `structure_rules_v2_6.json`
  - High-level guard rails: minimum score thresholds (`resolved_min=13`, `proto_min=8`, `tie_delta=3`), resolved structures list, and ties behaviour.
- `branch_tengods_policy.json`
  - Supplies Ten God distribution per branch, essential for core dominance checks and month-command support.
- `strength_policy_v2.json`
  - Provides `strength_state` and `score_normalized` inputs required by structure selectors and tie-breakers.
- `relation_policy.json` & `relation_aggregate_policy_v1.json`
  - Source of relation codes used in bonuses/penalties (`관인상생`, `살인상생`, `비겁탈재`, etc.).
- `elemental_projection_policy.json`
  - Supplies element vector alignment metrics referenced by certain patterns (e.g., 종격 requiring extreme distributions).

## Functional Requirements
1. **Evidence Preparation**
   - Gather Ten God vector (`branch_tengods_v1.1.ten_god_vector`), month command, strength state, relation events, element projection, and optional Yongshin alignment exactly as defined in policy selectors.
   - Ensure inputs carry policy version metadata for traceability.
2. **Scoring Engine**
   - Evaluate `core` conditions for each structure pattern using weightings specified (e.g., 정관 core weight 12.0 for dominance, 4.0 for month support).
   - Apply bonuses and penalties conditionally, respecting per-rule caps and residual guards.
   - Enforce breaker logic to mark patterns as 破格 when triggered.
   - Normalize raw scores via policy’s min/max mapping to 0-100.
3. **Status Resolution**
   - Assign status (成格/假格/破格) based on threshold coverage and breaker flags.
   - Apply priority order and tie-breakers: family priority → normalized score → month command fit → Yongshin alignment → deterministic hash.
   - Respect global guards from `structure_rules_v2_6.json` (resolved_min, tie_delta) before final selection.
4. **Output Schema**
   - Populate `AnalysisResponse.structure` with:
     - `primary`: `{ code, label, status, score, confidence, rationale, evidence }`.
     - `alternatives`: ordered list of runner-ups meeting proto threshold.
     - `policy_meta`: references to `gyeokguk_policy` and allied policies.
     - `debug`: optional detail for analysts (core hits, bonuses applied, penalties, breakers).

## Integration Notes
- Implement as `services/analysis-service/app/core/structure.py` exporting `StructureEngine.evaluate(context)`;
  context includes pillars, Ten God distribution, strength result, relation result, element vector, and yongshin outcome.
- Update orchestrator stage-3 pipeline to call the engine and pass the result into the response models instead of dropping it.
- Ensure recommendation guard (currently pointing to `StructureDetector`) reads the new `primary.code` field.

## Testing & Verification
- Unit tests per major structure (정관, 칠살, 정재, 편재, 식상, 인성, 비겁, 종재격, 종살격, 종관격) using policy-defined thresholds.
- Negative tests where breakers trigger 破格 (e.g., 관살혼잡 for 정관, 상관견관 for 칠살) to ensure demotion works.
- Snapshot tests comparing confidence and tie-breaking results on multi-candidate charts.
- Serialization test guaranteeing `AnalysisResponse.structure` passes Pydantic validation.

## Outstanding Items
- Confirm how 종격 families (CONG_*) should surface in UI (code vs localized label).
- Coordinate with narrative team to map `primary.code` into text templates before release.
- Decide whether to expose detailed evidence traces externally or keep behind diagnostics flag.
