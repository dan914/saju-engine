# KR Engine Addendum (Consolidated Functions & Formulas) — v2
Generated: 2025-09-26T14:37:07.617088Z

## Functions (new/updated)
- computeLMTOffset(lon_deg) -> seconds  // LMT_offset = lon_deg * 240.0
- applyLMTClock(utc, lon_deg) -> local_LMT  // 프로덕션 경로 미사용 (STD only)
- detectStructure(ctx) -> {primary?, candidates[], confidence}  // uses policies/structure_rules_v1.json
- evaluateClimate(ctx) -> {temp_bias, humid_bias, advice_bucket[]}  // policies/climate_map_v1.json
- applyRelations(ctx) -> {transform_to?:五行, boosts:[{element,k}]}  // policies/relation_transform_rules.json
- listShensha(ctx, proMode) -> {enabled, list[]}  // policies/shensha_catalog_v1.json
- computeLuckDirection(input) -> {direction, method, sex_at_birth?}  // policies/luck_policy_v1.json
- guardText(output, topic_tags[]) -> guarded_output  // policies/text_guard_policy_v1.json
- renderCautionBadges(ctx) -> string[]  // boundary/deltaT/structure_none, etc.

## Contracts updated
- Relation priority: sanhe_transform > sanhui_boost > chong > xing/po/hai > he_nontransform
- Sanhe transform: requires 3-complete or 2+month support, seasonal 旺/相, no strong conflict
- Sanhui: no transform; seasonal element boost only
- LMT: East +, West −; boundary clock only (no ephemeris shift)
- Evidence log: see schemas/evidence_log_addendum_v1.json

## Policies included
- relation_transform_rules.json
- structure_rules_v1.json
- climate_map_v1.json
- shensha_catalog_v1.json
- luck_policy_v1.json
- text_guard_policy_v1.json
- docs/lmt_spec.md
