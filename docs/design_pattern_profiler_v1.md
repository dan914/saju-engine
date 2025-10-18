# Pattern Profiler v1.0 — Design (Policy-Only, Deterministic)

## 1) 목적과 범위
Stage 1~3 엔진의 요약 출력을 입력으로 받아, 리포트/LLM/UI에서 재사용 가능한 **패턴 태그 집합(patterns[])**과
**요약 슬롯(briefs: one_liner, key_points[])**을 생성하는 정책 기반 모듈이다.
본 버전은 정책·스키마·테스트 산출물만 포함하며, 런타임 엔진은 후속 단계에서 정책을 로드해 매칭만 수행한다.

## 2) 입력/출력(개요)
- 입력: `engine_summaries_v1_1` 하위
  - `yongshin.primary` (목/화/토/금/수)
  - `strength.phase` ∈ {왕, 상, 휴, 수, 사}
  - `strength.elements.{wood,fire,earth,metal,water}` ∈ {low, normal, high}
  - `relation.flags` ⊂ {combine, sanhe, chong, harm}
  - `climate.balance_index` ∈ [-2..+2], `climate.flags` ⊂ {dryness, humidity}
  - `luck_flow.trend` ∈ {rising, stable, declining}
  - `gyeokguk.type` ∈ {정격, 종격, 화격, 특수}
- 출력:
  - `patterns[]` (최대 10개)
  - `briefs.one_liner` (한 줄, 120자 이하), `briefs.key_points[]` (최대 5개)
  - `policy_version`, `evidence_ref`(후속 구성; 예: `pattern_profiler/{luck_flow.trend}/{gyeokguk.type}`)

## 3) 규칙 설계 원칙
- **결정성**: 정책 JSON과 입력만으로 동일 결과 산출.
- **순차 매칭**: 규칙은 위→아래 평가, 태그는 누적.
- **안전성**: one_liner는 1줄/120자 이하, key_points는 최대 5개/문자열 80자 이하.
- **중립성**: 가치 판단 없이 구조적 상태만 태깅(강/약, 정합/부정합, 상승/하강 등).

## 4) 태그 카탈로그(요약)
- 일간 상태: `strong_daymaster`, `weak_daymaster`, `balanced_context`
- 용신: `yongshin_supported`, `yongshin_opposed`, `primary_high`, `primary_low`
- 관계: `relation_harmony`, `relation_conflict`
- 기후: `climate_aligned`, `climate_misaligned`, `balance_dry`, `balance_humid`
- 운의 흐름: `luck_rising`, `luck_stable`, `luck_declining`
- 오행 강조: `wood_emphasis`, `fire_emphasis`, `earth_emphasis`, `metal_emphasis`, `water_emphasis`
- 격국: `gyeokguk_pure`, `gyeokguk_mixed`

## 5) 브리프 템플릿
- 예: 상승 국면 → `" {yongshin.primary} 용신이 상승 흐름에서 지지를 받는 구간입니다. "`
- 변수 허용 목록: `yongshin.primary`, `luck_flow.trend`, `climate.balance_index`, `strength.phase`, `gyeokguk.type`

## 6) 가드 룰(LLM Guard 연동)
- `PATTERN-001` patterns ⊂ tags_catalog
- `PATTERN-002` one_liner 1줄/120자 이하
- `PATTERN-003` key_points ≤5, 각 ≤80자
- `PATTERN-004` evidence_ref 필수

## 7) 확장 계획
- 다중 템플릿 병합 우선순위(세분화)
- Pattern→Narrative 변환용 `Pattern Profiler v1.x` → Pattern-to-Text Mapper
- UI Evidence Viewer와 태그 필터 지원
