# Gyeokguk Classifier v1.0 — Design (Policy-Only, Deterministic)

## 1) 목적/범위
격국(정격/종격/화격/특수격)을 **정책 기반**으로 판정하는 엔진의 산출물 묶음.
본 버전은 정책·스키마·테스트만 제공하며 런타임 엔진은 후속에서 정책을 로드하여 규칙 매칭만 수행한다.

## 2) 입력/출력
- 입력(engine_summaries_v1_1):
  - yongshin.primary ∈ {목,화,토,금,수}
  - strength.phase ∈ {왕,상,휴,수,사}
  - strength.elements.{wood,fire,earth,metal,water} ∈ {low,normal,high}
  - relation.flags ⊂ {combine,sanhe,chong,harm}
  - climate.balance_index ∈ [-2..+2]
  - luck_flow.trend ∈ {rising,stable,declining}
- 출력:
  - type ∈ {정격,종격,화격,특수격}
  - basis[] (criteria_catalog의 서브셋, ≤5)
  - confidence ∈ [0,1]
  - notes ≤ 200자, 한 줄
  - policy_version, evidence_ref(후속 연결: `gyeokguk/{type}`)

## 3) 규칙 설계 요지
- 정격: 월령득기 + 용신상생 + 관계 순생(합/삼합) + 기후 균형(≥0)
- 종격: 일간 극약(phase ∈ {휴,수,사}, primary=low) + 충(沖) + 기후 불리(≤0)
- 화격: 합화/삼합 + 기후 보정(≥1) + primary 정상(normal)
- 특수격(양인/건록): 강한 일간(왕) + 특정 관계(harm 등) + 용신 범주(목/화)

## 4) 결정성
- 규칙은 위→아래 순서로 최초 일치 1건 채택.
- JSON은 RFC-8785 정규화 + PSA 서명(`policy_signature`)을 가정.

## 5) 테스트 전략
- policy.examples 4건으로 end-to-end 모의평가.
- 규칙 emit의 basis⊂criteria, confidence∈[0,1], notes 길이 확인.

## 6) 확장 계획
- 세부 특수격(양인격/건록격/종아격 등) 분기 추가
- Luck Flow 트렌드 가중치 반영(보조 근거)
- Evidence Builder 연계: `evidence_ref = "gyeokguk/{type}"` 명시
