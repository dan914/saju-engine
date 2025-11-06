# Luck Engine v1.1.2 Seed Mapping

This note tracks what the current `SajuOrchestrator` emits today and what the
new v1.1.2 luck calculators expect as input.  It forms the checklist for the
upcoming seed-builder work.

## 1. Orchestrator Output (2025-10 build)

Top-level structure from `SajuOrchestrator.analyze()` (see
`services/analysis-service/app/core/saju_orchestrator.py`).

| Block                        | Path in result            | Notes |
|-----------------------------|---------------------------|-------|
| Strength summary            | `strength`                | Includes `score_raw`, `score`, `score_normalized`, `grade_code`, `bin`.
| Ten gods analysis           | `ten_gods`                | Stem-level relationships + aggregated hidden counts.
| Relation hits               | `relations`               | Priority string + `notes` like `chong:巳/亥`.
| Relation weights            | `relations_weighted.items`| Structured list with `type`, `participants`, `impact_weight`, `confidence`.
| Relation extras             | `relations_extras`        | Banhe/five-he/zixing counts.
| Combination element         | `combination_trace`       | Element transformations already applied to raw distribution.
| Element balance (raw)       | `elements_distribution_raw`| 5-element proportions after hidden stem selection.
| Climate evaluation          | `climate`                 | Temperature/humidity bias, used by stage-3.
| Yongshin selection          | `yongshin`                | Primary/supporting 용신; same data drives categorical hints.
| Stage-3 engines             | `stage3`                  | Luck flow, 격국 classifier, pattern profiler, etc.
| Decade luck (대운)          | `luck`                    | v1.0 policy output (`pillars`, `start_age`, `direction`, etc.).
| Void / Yuanjin              | `void`, `yuanjin`         | Already aligned to evidence builder.
| Evidence, summaries, locale | `evidence`, `engine_summaries`, `_enrichment` | Downstream only; not needed for raw luck components.

Data **not** currently produced:

- No frame-by-frame (year/month/day) structures.
- No explicit transit pillars for years/months/days.
- No 태세 branch information.
- No numeric gate norms (only the stage-3 luck flow trend, unrelated to gates).
- No geokguk follow-type summary beyond classifier output.

## 2. Luck Engine v1.1.2 Expectations

Each calculator (`AnnualLuckCalculator`, `MonthlyLuckCalculator`,
`DailyLuckCalculator`) expects a `ChartContext` with:

- `strength_scalar` in [-1, +1] plus `strength_profile` (weak/neutral/strong).
- `element_balance` and `hidden_stems` for natal pillars.
- `frame_seeds[level]` providing structured inputs:
  - `sibsin`: per-ten-god exposures, including hidden tiers (`main/middle/minor`).
  - `relations`: list of events with `kind`, `magnitude`, optional `bonus_keys`.
  - `axis_patterns`: explicit 사정충/삼형 detections with state and emit flag.
  - `pilar_overlap`: flags for same/reverse pillar stacking.
  - `taese`: 태세 relation entries (`relation`, `magnitude`, `synergy`).
  - `season`: branch, element for seasonal scoring.
  - Optional `transform_effects`, `unseong_stage`, `gates`, `events`.

Additional chart-level hints:

- `geokguk_detect`: `{stage, follow_type, confidence}` for category overlays.
- Hap transform descriptors for 합화 (mapped to `transformation_role_coeff`).
- Gate inputs (`daewoon_norm`, `year_norm`, `month_norm`) for hierarchy.

## 3. Proposed Mapping (confirmed for implementation)

1. **Timeline & transit pillars**
   - Use luck-pillar sequence to locate the active decade; derive annual/monthly/day pillars via standard 60갑자 stepping.
   - Month windows reuse existing solar-term loader.

2. **Strength scalar**
   - Compute `(strength.score_normalized - 50) / 50`, clamp to [-1, 1].
   - `strength_profile` maps directly from `strength.bin`.

3. **Ten-god exposures**
   - Natal exposures: take `ten_gods.by_pillar[slot]`;
     hidden tiers map `primary→main`, `secondary→middle`, `tertiary→minor`.
   - Transit exposures recomputed on the fly using existing ten-god policy.

4. **Relations**
   - Base event list on `relations_weighted.items` (fallback to `relations.notes`).
   - `kind` normalization: `chong→chung`, `sanhe→hap`, `liuhe→hap`, `xing→hyeong`,
     `hai→hae`, `pa` stays `pa`.
   - `magnitude` from `impact_weight` (default 1.0 if missing).
   - Bonus detection: double clash, 태세 synergy, 삼합 완결, 간합 변환.

5. **Axis patterns**
   - Detect 사정충 (四正 clash) and 삼형 groups from branch sets.  Emit `complete` if all required branches present, `partial` for partial matches.

6. **태세 & season**
   - 태세 branch determined from the annual pillar; compare with transit branch to produce relation entry.  Apply 0.5 attenuation when day master is `weak` and event targets resource/peer roles.
   - Season uses policy matrix: branch-element weight × strength factor (per level).

7. **Gates**
   - Parent norms derived from the previous frame’s normalized score (scale ±100).
   - `daewoon_norm` uses decade-level normalized value (set 0 when unknown).

8. **Hap transform & geokguk**
   - When `relations.transform_to` exists, add `{ "to": "to_fire", "confidence": weight }` to `transform_effects` and populate `unseong_stage` accordingly.
   - Stage-3 격국 classifier yields `stage` & `classification`; map to policy `follow_type` and forward the provided confidence.

9. **Category overlays**
   - 상관견관 guard triggers when Ten-god breakdown shows 상관 dominance over 관 in monthly/daily seeds; ratio check uses seed exposures.

These rules let us build a deterministic `LuckSeedBuilder` without external references.

## 4. Next Implementation Steps

1. Implement `LuckSeedBuilder` module that consumes orchestrator results and
   emits the v1.1.2 `ChartContext` (covering year/month/day frames).
2. Integrate the new calculators in the orchestrator after the seed builder.
3. Expose outputs (scores, categories, recommendations, alerts, explain) through
   API/LLM/report schemas and adjust regression fixtures.
