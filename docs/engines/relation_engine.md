# Relation Engine Restoration Guide

## Purpose
The Relation Engine is responsible for detecting 六合/三合/半合/三會/刑/破/害/沖 interactions across the four pillars, producing both structural evidence and UI content. Current orchestration only surfaces `priority_hit` and discards the full relation set, leaving front-end views empty. This guide outlines how to rebuild the engine interface and align it with policy contracts.

## Policy Landscape
- `relation_policy.json` (version 1.1)
  - Defines conservation budget using hidden stem weights, relation fusion rules, confidence formula, and detailed line items per relation type with scores and priorities.
  - Provides element mappings (branch, triad, liuhe, banhe) used for downstream element projections.
- `relation_aggregate_policy_v1.json`
  - Aggregates relation impacts for strength/structure adjustments with caps per type and total.
- `relation_structure_adjust_v2_5.json`
  - Applies structure-specific adjustments (e.g., 칠살 격 gains or penalties from 合/沖 events) after structure resolution.
- `school_profiles_v1.json`
  - Supplies profile-based caps (`total_abs_max`) and toggles (e.g., transform gates for 삼합) that must be honoured when generating outputs.
- `elemental_projection_policy.json`
  - Relies on relation traces to adjust element vectors; maintain trace schema compatibility.

## Functional Requirements
1. **Detection Pipeline**
   - Enumerate all branch pairs/triads with month branch awareness.
   - Apply policy fusion rules: 三合 consumes 3 units, 六合 consumes 2, etc., respecting conservation and mutual exclusion (e.g., 三合 outranks 半合).
   - Track destructive relations (沖/刑/破/害) with priority weighting and month multipliers.
   - Support hidden stem-aware budgeting as dictated by `budget_mode = hidden_stems_v1`.
2. **Output Contract**
   - Return structured lists for each relation family:
     ```json
     {
       "relations": {
         "he6": [...],
         "sanhe": [...],
         "banhe": [...],
         "sanhui": [...],
         "chong": [...],
         "xing": [...],
         "po": [...],
         "hai": [...]
       },
       "priority_hit": {...},
       "trace": {...},
       "policy_meta": {...}
     }
     ```
   - Each entry includes involved pillars (stem+branch), resulting element (if applicable), score, confidence, polarity (favour/risk), and textual labels.
   - Provide aggregate metrics: conservation_ok flag, conflict ratio, and total absorbed budget for downstream use.
3. **Configurability**
   - Honour school profile caps (`relation_caps.total_abs_max`).
   - Support toggles for 삼합 transforms (currently disabled outside lab scope) and ensure invariants (no double deduction) are enforced when enabled.
4. **Integration Hooks**
   - Expose relation trace to Element Engine (for `relation_v1.0` projector) and Structure Engine (for bonuses/penalties defined in `gyeokguk_policy.json`).
   - Ensure RelationResult serialises via `AnalysisResponse.relations`; update Pydantic model accordingly.

## Implementation Steps
- Refactor relation logic into a dedicated module (e.g., `core/relation_engine.py`) wrapping the existing policy-driven transformer (if present in `services/analysis-service/app/core/relations.py`).
- Modify `saju_orchestrator._call_relations` to return the full result instead of slicing out `priority_hit`.
- Map relation entries to localisation keys defined in `relation_policy` for KO/EN front-end rendering.
- Provide fallback handling when conservation budget is exceeded (mark as unstable per policy `unstable_flag`).

## Testing Plan
- Unit tests per relation type (六合, 三合, 半合, 沖, 刑, 破, 害) using crafted charts to cover every branch combination.
- Conservation invariant tests: total consumed units equals produced units when transformations fire.
- Regression comparison against known examples (e.g., 巳酉丑金局, 子午冲) verifying score and confidence align with policy values.
- Schema tests to ensure `RelationResult` populates arrays and contains no `None` placeholders.

## Open Items
- Confirm whether hidden stem-based budgeting should deduct from branch availability when multiple relations overlap (policy allows zero leakage; implementation must enforce order).
- Decide on tie-breaking for simultaneous positive and negative relations affecting the same pillars (policy suggests attenuation factors; implementation detail to finalise).
