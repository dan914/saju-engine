# Saju Engine 작업 목록 (Codex 번들 v1 기준)

## 1. Pillars Core 엔진
- [x] resolveLocalToUTC 구현
  - [x] IANA tzdb 역사 이력(DST 포함) 조회 모듈 연동
  - [x] 자시 23:00 기준 day boundary 계산(LCRO·ε=1ms) 적용
  - [x] timezone 이벤트(trace 플래그) 생성 및 검증 케이스 작성
- [x] getMonthBranch 구현
  - [x] 절입(12절) 테이블 로더 연결
  - [x] 월지/계절 매핑 로직 검증(입춘=寅월 시작)
  - [ ] 골든셋 경계 케이스 추가(절입 ±1h)
- [x] calcPillars 구현
  - [x] 오호둔(연간 그룹) 테이블 적용
  - [x] 오서둔 시간간 전개 + 60갑자 매핑 함수 작성
  - [x] 연/월/일/시주 결과 통합 + trace 경계 플래그 처리
- [ ] mapWangState 구현
  - [x] `policy/seasons_wang_map.json` 로드 및 캐싱
  - [x] 월지별 오행 旺/相/休/囚/死 판정 함수 작성
  - [x] 단위 테스트(12지 × 5행 검증) 추가
- [x] scoreRootSeal 구현
  - [x] `policy/seasons_wang_map.json`, `policy/strength_criteria_v1.json` 참조 구조 정의
  - [x] 장간 추출(zanggan_table) + 득근/득생 판단
  - [x] 강약 계산 기준에 따른 점수 산출 함수 작성
- [ ] scoreStrength 구현
  - [ ] 월령/통근/투간/합충 보정 규칙 적용
  - [ ] 결과 레벨(强/中强/中/中弱 등) 산출
  - [ ] 회귀 테스트(골든셋 ≥200) 준비
- [x] buildEvidenceLog 구현
  - [x] `templates/evidence_log.example.json` 스키마 기반 필드 매핑
  - [x] Trace, ΔT, tz 이벤트, 경계 근거 포함
  - [x] LLM 전달용 JSON 검증 스크립트 추가
- [ ] Explain Layer 통합
  - [ ] `rules/` 디렉터리의 평가/라벨 로딩
  - [ ] Polisher/Checker 프롬프트 입력 계약 정리
  - [ ] 수치 불변 검증 훅 구현

## 2. ΔT & 타임존 운영
- [x] ΔT 정책 적용
  - [x] `policy/deltaT_policy_v1.json` 파서 및 모듈화
  - [x] `scripts/dt_compare_skeleton.py` 연동해 민감도 검증 파이프라인 구축
  - [ ] ΔT 회귀 결과를 Trace에 반영 (TODO)
- [ ] 타임존 회귀 파이프라인
  - [ ] `scripts/tzdb_regress.py` workflows/CI 연결
  - [ ] `data/tzdb_samples.csv` 기반 테스트 자동화
  - [ ] tzdb 버전 업데이트 모니터링 + Slack/알림 훅 설계

## 3. 데이터/룰셋 정비
- [ ] 절기 테이블(1600–2200) 정제 및 검증
  - [ ] CSV/Parquet 변환 및 로더 성능 테스트
  - [ ] Astronomy Engine 결과와 diff 비교(±1s 허용)
- [ ] 규칙 JSON 검증
  - [ ] `rulesets/` 및 `policy/` 스키마 정의(jsonschema)
  - [ ] CI에 룰셋 린터 추가
  - [ ] 버전업 체인지로그 작성 절차 정의

## 4. 테스트 & CI
- [ ] 골든셋 ≥200 구축
  - [ ] 경계/타임존/연대/ΔT 케이스 수집
  - [ ] 자동 검증 스크립트 작성(pytest + snapshot)
  - [ ] 차이 > 1s 발생 시 Fail 규칙 적용
- [ ] GitHub Actions 강화
  - [ ] ΔT / tzdb 회귀 워크플로 통합
  - [ ] 서비스별 커버리지 리포트 업로드
  - [ ] 배포 게이트(성능 P95, 회귀 통과) 자동화

## 5. UI/스토어 문구
- [ ] `docs/store_policy_copy_kr.md` / en.md 최신 정책 반영
- [ ] `templates/ux_footnote_template.md` 제품별 각주 형식 적용
- [ ] 앱/웹 UI에 규칙 버전, ΔT, 타임존 이벤트 표기 확인

## 6. 문서/운영
- [ ] ΔT 운영 가이드 문서화 업데이트(`docs/deltaT_operational_guide.md`)
- [ ] tzdb 회귀 정책 문서 검토(`docs/tzdb_regression_policy.md`)
- [ ] evidence log 운영 절차 정리(`templates/evidence_log.example.json` 기준)
## 7. Addendum v2 follow-ups
- [x] relation_transform_rules 적용 (sanhe/sanhui 우선순위, 변환/boost 로직)
  - [x] sanhe 변환 조건 구현 및 테스트
  - [x] sanhui seasonal boost 적용
  - [x] relation priority 단위 테스트
- [x] structure_rules 기반 격국 판별
  - [x] detectStructure 함수 설계 및 mock 테스트
  - [ ] 분석 서비스 통합 계획 수립
- [x] climate_map 기반 기후 평가
  - [x] evaluateClimate 함수 구현
  - [x] evidence_log 기후 섹션 추가
- [x] luck_policy & shensha_catalog 반영
  - [x] 운 방향 computeLuckDirection 프로토타입
  - [x] listShensha 옵션 관리 지침
- [x] text_guard_policy 연동
  - [x] guardText 필터 로직 초안
  - [x] LLM 출력 후 검증 훅 연결
- [x] evidence_log 스키마(추가분) 검증
  - [x] schemas/evidence_log_addendum_v1.json 대비 validation 추가
  - [ ] 새로운 필드(경고 배지 등) 매핑 계획
- [x] LMT 관련 QA/회귀
  - [x] STD vs LMT 비교 회귀 테스트 설계
  - [x] telemetry 알림 시나리오 정의
## 8. Addendum v2.1 follow-ups
- [x] time_basis_policy 반영 (STD only 정책 확인)
  - [x] LMT 배제 CI 가드 유지/보강
  - [x] evidence_log에 time_basis 표기 추가
- [x] zi_boundary_policy 적용 검토
  - [x] split-zi 옵션이 비활성 상태인지 확인
- [x] seasons_wang_map_v2 반영
  - [x] 四季土=旺 지도 업데이트
  - [x] strength_scale_v1_1 스코어 조정 적용
- [x] relation_transform_rules_v1_1 확장
  - [x] banhe_boost 로직 구현
  - [x] five_he_transform 인터프리테이션 적용
  - [x] zixing_rules self-penalty 연동
- [x] luck_start_policy 적용
  - [x] computeLuckStartAge 함수 작성
  - [x] ΔT/boundary 배지 계산
- [x] recommendation_policy 반영
  - [x] Yongshin 제안 로직 가드
  - [x] advisory copy 템플릿 준비
- [x] evidence_log_addendum_v1_1 대응
  - [x] month_stem_effect/banhe/five_he/zixing/ seal_validity 필드 추가
  - [x] day_boundary_policy/time_basis 기록
## 9. Addendum v2.3 follow-ups
- [x] root_seal_policy_v2_3 적용 (we U location bonus & validity)
  - [x] wealth_location_bonus_total 계산/캡
  - [x] wealth_breaks_seal/suppressed_by_officer 판정
- [x] evidence_log v1.3 필드 기록
  - [x] seal_validity.wealth_location_* 필드 매핑
- [x] dt_compare.py 정책 연동
- [ ] checklist_v2_3 시나리오 회귀 실행
## 10. Addendum v2.4 follow-ups
- [ ] time_basis/zi boundary 정책 재확인 (v2.4 bundle)
- [ ] strength_adjust_v1_1 반영 (월령/합충 보정)
- [ ] structure_rules_v1_2 및 relation_structure_adjust 적용
- [ ] deltaT_trace_policy_v1 적용 + evidence/trace 갱신
- [ ] telemetry_policy_v1_1 구현 (LMT 및 경계 이벤트 모니터링)
- [ ] evidence_log_addendum_v1_4 대응
- [ ] explain_templates_v1.json 기반 Explain Layer 구축
## 11. Addendum v2.5 follow-ups
- [ ] school_profiles_v1 적용 (classic/practical/sanhe profiles)
- [ ] relation caps 및 five_he scope 프로파일 반영
- [ ] deltaT_trace_policy_v1_2 동작 검증
- [ ] evidence_log_addendum_v1_6 확장 (school_profile, five_he post effects, structure_v2)
- [ ] telemetry_policy_v1_3 이벤트 처리
- [ ] structure_rules_v2_6 및 relation_structure_adjust 반영
- [ ] goldens manifest v2_6 기반 회귀 추가
## 12. Addendum v2.6 follow-ups
- [ ] school_profiles_v1 적용 (default=practical_balanced, Pro 전용 switching)
- [ ] five_he_policy_v1_2 적용 (Lab/Pro 구조 변환)
- [ ] deltaT_trace_policy_v1_2 strict 모드 + boundary 링크 구현
- [ ] telemetry_policy_v1_3 이벤트 처리 (profile, five_he lab transform, structure tie)
- [ ] evidence_log_addendum_v1_6 매핑 (school_profile, five_he.post_effects, structure_v2.resolved_at_version, deltaT.model/source)
- [ ] goldens manifest v2_6 회귀 구성

## 13. Analysis API Integration
- [ ] AnalysisResponse 스키마 확장
  - [ ] orchestrator 출력 필드(relations_weighted, relations_extras.banhe_groups, ten_gods/twelve_stages, stage3, evidence, engine_summaries, void, yuanjin 등) 반영
  - [ ] `_map_to_response`를 갱신해 엔진 결과를 그대로 전달하고 placeholder 제거
  - [ ] `/analyze` response_model 및 LLM Guard 훅 검증
- [ ] 정책 및 테스트 실거래화
  - [ ] 사라진 정책 경로를 최신 번들로 업데이트하고 서명 검증 재활성화
  - [ ] `test_relation_policy.py` 등 스킵 테스트 재가동 및 전체 pytest(695개) 통과 확인
- [ ] 골든셋 커버리지 상승
  - [ ] kr_core_regressions 추가 생성(+118)
  - [ ] school_profiles / five_he_lab / zongge_guard 케이스 채우기
  - [ ] 골든셋 실행을 CI 회귀 워크플로에 편입

## 14. Analysis-Service Test Failures (2025-10-25)
- [x] LLMGuard 빈 구조 대응
  - [x] `test_llm_guard.py` 전용 요청 생성 헬퍼 추가(실제 pillars 사용)
  - [x] guard.postprocess 호출부에서 `structure_primary` None 대응
- [x] LLMGuard Korean Enricher 통합 검토
  - [x] `LLMGuard.default()`에 KoreanLabelEnricher 주입 필요성 평가
  - [x] 테스트 기대(`_enrichment`, `korean_labels_added`) 현실화 or 기대값 조정
- [x] StructureDetector 테스트 갱신
  - [x] `test_structure.py` confidence / candidates 기대치를 최신 정책에 맞게 수정
- [x] Lifecycle schema 동기화
  - [x] lifecycle_stages.schema.json에 variant / weights / damping / mirror_overlay 허용
  - [x] `test_lifecycle_schema_validation.py` 통과 확인
- [x] Strength 계산 테스트 정리
  - [x] `test_strength_normalization_fix.py` 등 기대값 재검토 및 업데이트
- [x] MasterOrchestrator 테스트 수정
  - [x] Stage3 스텁 도입으로 dict 컨텍스트 대응
  - [x] 해당 테스트 재실행으로 회귀 확인

## 15. Luck Engine Expansion (Annual/Monthly/Daily)
- [ ] AnnualLuckCalculator 스캐폴딩
  - [x] `services/common/saju_common/engines/annual.py` 생성 및 `EngineOptions`, `ChartContext`, `LuckFrame` 형식 정의
  - [x] 절입 기반 연 경계 계산 유틸 구현(`FileSolarTermLoader`, `BasicTimeResolver` 사용)
  - [x] 연간 상호작용/십신/계절 스코어링 초기 버전 작성
- [ ] MonthlyLuckCalculator 스캐폴딩
  - [x] `services/common/saju_common/engines/monthly.py` 생성 및 연계 옵션 처리
  - [x] 연운 스코어 연동(α 계수) + 월 상호작용/십신 가중치 적용
  - [x] good_days/caution_days 후보 추출 구조 준비
- [ ] DailyLuckCalculator 기초 구현
  - [x] `services/common/saju_common/engines/daily.py` 생성, 일진 계산 및 월운(β) 연계
  - [ ] 일간 장간·합충 반영 점수 계산, clamp 처리
  - [ ] 설명 drivers 구조 정의
- [ ] 공용 유틸/스코어러 정리
  - [x] `services/common/saju_common/engines/utils/` 디렉터리 생성, 60갑자/상호작용 헬퍼 분리
  - [x] `scoring.py`에 정책 JSON 로더 및 α/β/클램프 처리 구현
  - [x] `__init__.py` 업데이트로 신규 엔진 export
- [ ] Strength 프로필 판정 로직 구현(신강/중간/신약) 및 정책 가중 연동
- [x] 연 경계(입춘 vs 설) UX/옵션 정의 및 메타 반영
- [x] 상호작용 계산 구조 재정비(본명 vs 운 계층 분리, 중복 가중 방지)
- [ ] 정책 파일 초안 작성
  - [x] `policy/luck_annual_policy_v1.json`, `policy/luck_monthly_policy_v1.json`, `policy/luck_daily_policy_v1.json` 추가
  - [x] 십신/상호작용/계절 가중치 및 α/β 설정 명시
  - [ ] policy guards + jsonschema 작성 및 테스트 연결
- [ ] API 통합 초기 작업
  - [ ] `/api/v1/luck/annual` 엔드포인트 구현 및 캐시 키 지정
  - [ ] monthly/daily 엔드포인트 뼈대 추가, 공통 응답 메타 구조 확정
  - [ ] orchestrator 및 analysis pipeline에 연/월/일 운 결과 주입
- [ ] 테스트/QA 준비
  - [ ] 연/월/일 운 단위 테스트 케이스(절입 경계, 자시 경계 포함)
  - [ ] 통합 테스트에서 `analysis.luck.years/months/days` 출력 검증
  - [ ] 정책/경계 회귀 스위트 및 캐시 멱등성 테스트 설계
