# Addendum v2.1 — Decisions after peer review
Generated: 2025-09-26T15:10:35.943995Z

## New/Updated Policies & Functions

### Time basis / Boundary
- `time_basis_policy_v1.json`: **STD only**, tzdb+DST; LMT banned in production.
- `zi_boundary_policy_v1.json`: default unified Zi(23:00–01:00); Lab-only split-zi (prev-day 23:00–23:59).

### Deukryeong & Strength
- `seasons_wang_map_v2.json`: **四季土=旺** map synchronized.
- `strength_scale_v1_1.json`: points for 旺/相/休/囚/死 + **month_stem_adjust pct** + **seal_validity_checks**.

### Relations
- `relation_transform_rules_v1_1.json`: adds **banhe_boost** (2 members + seasonal support), refines **five_he_transform** (interpretation-only).
- `zixing_rules_v1.json`: self-penalty gates (conditional).

### Luck
- `docs/luck_start_policy.md`: start age **= days_to_next_jieqi / 3.0** (standard), with ΔT/boundary badges.

### Recommendation Gating
- `recommendation_policy_v1.json`: **Do not auto-propose Yongshin** without structure; show advisory copy instead.

### Evidence
- `schemas/evidence_log_addendum_v1_1.json`: records month_stem_effect, banhe, five_he, zixing, seal_validity, day_boundary_policy, time_basis.

## Suggested Functions
- `assessDeukryeong(ctx)` -> { status_by_element, daymaster_status }
- `adjustStrengthByMonthStem(ctx)` -> pct delta, reasons
- `applyRelationEffects_v11(ctx)` -> {transform_to?, boosts[], banhe?}
- `checkZixing(ctx)` -> {triggered, reasons[]}
- `computeLuckStartAge(ctx)` -> float (years), per policy
- `recommendYongshin(ctx)` -> gated output per recommendation policy

