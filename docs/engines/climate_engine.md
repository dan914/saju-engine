# Climate Engine Modernisation Notes

## Objective
Replace the stubbed climate lookup in `services/analysis-service/app/core/climate.py` with a policy-driven evaluator that produces temperature/humidity states, biases, and recommendations aligned with downstream engines (strength, element projection, Yongshin).

## Policy References
- `saju_codex_addendum_v2/policies/climate_map_v1.json`
  - Primary data source: month branch segmented into 초/중/말 with `temp` and `humid` tags (`cold/hot/warm/mild/cool` and `dry/neutral/humid/wet`).
- `strength_policy_v2.json`
  - Uses climate segments (`寒/熱/燥/濕`) to adjust 득세 scores; Climate Engine must map raw biases to these segments.
- `elemental_projection_policy.json`
  - `climate_balancer_v1.0` projector adds element bias (e.g., cold → boost 火, dry → boost 水); requires consistent input schema.
- `yongshin_policy.json`
  - Weighs climate component at 10%; expects structured evidence fields indicating temperature and humidity states.
- `telemetry_policy_v1_3.json`
  - Defines logging/trace requirements for environmental evidence; ensure compliance when emitting climate diagnostics.

## Functional Requirements
1. **Segmentation Logic**
   - Determine seasonal segment (초/중/말) using solar terms (절기) derived from birth datetime (requires jieqi dataset; see `gyeokguk_policy` dependencies).
   - Pull temperature/humidity bias for the specific month branch and segment from `climate_map_v1.json`.
2. **State Mapping**
   - Translate qualitative tags to normalized enums for downstream policies:
     - Temperature → `寒/涼/溫/熱` etc.; ensure compatibility with `strength_policy_v2.deukse.climate_adjust` segments (`寒`, `熱`, `燥`, `濕`).
     - Humidity → map to moisture axis (`燥`, `濕`, `中`).
   - Provide derived recommendations (e.g., increase Water to combat dryness) referencing Element Engine outputs.
3. **Output Contract**
   - Return structure such as:
     ```json
     {
       "temperature": {"raw": "cold", "mapped": "寒", "score": -3},
       "humidity": {"raw": "dry", "mapped": "燥", "score": -2},
       "element_bias": {"advise": ["水","木"], "penalize": ["火"]},
       "confidence": 0.8,
       "policy_meta": {...}
     }
     ```
   - Include `segment` (초/중/말), `month_branch`, and evidence references.
4. **Edge Handling**
   - If birth place/timezone missing, fall back to default regional averages and flag reduced confidence.
   - Accommodate leap months and 子時 rollover (ensure day boundary aligns with pillars service corrections).
   - Support future overrides via config (e.g., manual climate bias adjustments from UI).
5. **Observability & Safety**
   - Adhere to telemetry policy: emit structured logs only when diagnostics enabled.
   - Provide deterministic outputs (no randomness), enabling consistent regression tests.

## Integration Tasks
- Rewrite `ClimateEvaluator` to load policy via `resolve_policy_path` (remove hardcoded path).
- Expose `evaluate(birth_context)` returning the structured payload above; orchestrator should inject it into analysis context so Strength, Element Projection, and Yongshin engines can consume it.
- Update tests in `services/analysis-service/tests/test_climate.py` (create if missing) to validate mapping and fallback behaviour.

## Testing Checklist
- Unit tests for each month branch boundary (e.g., 辰월 초/중/말) verifying temperature/humidity mapping.
- Integration tests across representative charts to confirm climate adjustments propagate into Strength and Element Projection outputs.
- Regression fixture ensuring 子時 boundary (23:30 births) select correct segment once pillars service fixes are applied.

## Open Questions
- Confirm whether regional overrides (latitude-based adjustments) are required now or can be deferred.
- Determine if humidity `wet` should map to `濕` or a higher-order category when combining with temperature.
- Coordinate with policy owners on timeline for `climate_map_v1` signature finalisation; current file shows version `1.0` with no checksum.
