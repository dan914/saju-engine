# Element Engine Rebuild Blueprint

## Purpose
The Element Engine produces the five-elements distribution that powers Yongshin selection, strength balancing, narratives, and UI visualisations. The current calculation in `services/analysis-service/app/core/saju_orchestrator.py` counts four visible stems at weight 1.0 and branches at 0.5, ignoring hidden stems and policy-driven adjustments. This document captures the authoritative requirements for rebuilding the engine in line with the signed policies.

## Required Inputs
- Resolved pillars (year/month/day/hour) with both visible stems and branches.
- Hidden stem decomposition per branch using `branch_tengods_policy.json` (`role_weights.primary=1.0`, `secondary=0.6`, `tertiary=0.3`).
- Calendar context: timezone-adjusted birth datetime, leap-month flag, 子時 rollover indicator.
- Optional school override (`school_profiles_v1.json`) to support alternative caps (e.g., `sanhe_strict`).
- Policy metadata (version, signature) injected via `services.common.policy_loader` for audit.

## Core Policy References
- `saju_codex_batch_all_v2_6_signed/policies/elements_distribution_criteria.json`
  - Mode `branch_plus_hidden`; stems weight 1.0, branches 1.0, hidden stems weighted 1.0/0.5/0.3 by role.
  - Threshold labels (`과다/발달/적정/부족`) and rounding to two decimals; honours conservation when relation transforms are enabled.
- `branch_tengods_policy.json`
  - Provides hidden stem roster for each branch and defines aggregation rules for Ten Gods; reuse its `role_weights` and localisation strings for branch-level reporting.
- `seasons_wang_map_v2.json`
  - Supplies 旺相休囚死 states per month branch; use to expose seasonal annotations in the element breakdown (e.g., "Metal 旺 in 酉 month").
- `school_profiles_v1.json`
  - Governs caps for relation-driven adjustments and future transform toggles; default profile `practical_balanced` must be respected.
- `elemental_projection_policy.json`
  - Downstream consumers expect the element vector produced here to align with this policy’s projector inputs; keep vector ordering `木火土金水` and ensure values are percentages summing to 100.

## Functional Requirements
1. **Weighting Pipeline**
   - Count visible stems with configurable weight (default 1.0).
   - Count branches using container element weight 1.0; maintain a lookup map separate from hidden stems to avoid double counting.
   - Decompose each branch into hidden stems via policy, applying role weights and matching Ten God relationships against the day stem polarity.
   - Provide hooks for relation transforms (`relation_transform` block) but keep disabled until `apply=true` is signed off.
2. **Normalization & Labelling**
   - Produce raw totals and normalized percentages (`sum(percentages)=100` within ±0.01 tolerance).
   - Attach classification labels per element using threshold table; expose multi-locale strings.
   - Include seasonal state annotation (旺相休囚死) and the contributing pillars (stem/branch/hidden counts) to support analysts.
3. **Configurability**
   - Load weights and thresholds at runtime; fail fast if policy versions mismatch expected signature.
   - Allow per-school overrides without redeploying code (read from policy or env var).
4. **Observability**
   - Emit structured trace (e.g., `element_engine.debug`) with subtotal per pillar segment.
   - Include policy version and checksum in the response for audit trails.

## Integration Requirements
- Replace `_calculate_elements` in `saju_orchestrator.py` with a dedicated `ElementEngine` service under `services/analysis-service/app/core/elements.py`.
- Update orchestrator wiring so the engine returns:
  ```json
  {
    "element_vector": {"木":24.0,"火":18.0,"土":22.0,"金":16.0,"水":20.0},
    "raw_totals": {...},
    "breakdown": {"stems": {...}, "branches": {...}, "hidden": {...}},
    "labels": {...},
    "seasonal_states": {...},
    "policy_meta": {...}
  }
  ```
- Ensure Yongshin selector and Strength engine consume the updated vector without reshuffling element order.
- Preserve backwards compatibility for clients by providing a flattened percentage view while we migrate the API schema.

## Testing & Validation
- Regression fixtures for canonical charts (e.g., `甲子`, `庚辰`, `乙酉`) comparing against policy-calculated percentages.
- Edge cases: dual hour (子時) rollover, leap month, void branches, all-hidden support charts.
- Unit tests verifying policy thresholds and localisation labels.
- Contract test ensuring output percentages feed correctly into `elemental_projection_policy` projectors (cosine similarity >0.99 against expected vectors).

## Outstanding Questions
- Relation-driven element transforms (`三合/半合` boosts) remain disabled in policy; confirm roadmap before implementation.
- Confirm whether school profile selection is user-driven (UI toggle) or deployment config.
- Determine canonical rounding strategy for hidden stem fractions when reporting pillar contributions (policy suggests two decimals; need frontend confirmation).
