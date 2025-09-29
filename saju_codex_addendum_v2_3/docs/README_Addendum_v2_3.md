# Addendum v2.3 — Wealth-breaks-Seal 위치 가중 보강
Generated: 2025-09-27T02:17:18.536568Z

## What changed (delta from v2.2)
- `root_seal_policy_v2_3.json`: Adds `wealth_location_bonus` (월/일/시 지지 위치 + 월간 노출 보정, cap=2.0).
- Evidence v1.3: New keys under `seal_validity` to log how 위치 보정이 적용되었는지.
- Bundles `yugi_policy_v1_1.json` (월지 余氣 승격표) for consistency.

## How to integrate
1) Load `policies/yugi_policy_v1_1.json` (ensure zanggan_table v1.0) → apply elevation in month branch only.
2) Update RootSealScorer:
   - Compute root_score for 재/인.
   - Compute `wealth_location_bonus_total` if 재성 has ≥sub roots in 月/日/時; add `month_stem_exposed_bonus` when applicable; cap at 2.0.
   - Apply `wealth_breaks_seal` formula & side conditions.
3) Emit evidence per `schemas/evidence_log_addendum_v1_3.json`.
4) Regression tests:
   - (A) 재성 월지sub + 일지sub + 월간노출: bonus=1.5+1.0+0.5=3.0 → capped to 2.0.
   - (B) 余氣-only case: bonus=0 (min_level=sub).
   - (C) 월상태 旺/相 없이 단순 위치만 강한 경우: formula 충족해도 side condition로 반려.

## Backward compatibility
- Set `wealth_location_bonus.enabled=false` to revert to v2.2 behavior.
