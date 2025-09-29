
# Saju Engine — Codex Handoff Bundle (v1)
Generated: 2025-09-26T10:10:19.704079Z

## Structure
- policy/: Core policies (왕상휴수사 맵, 강약 기준, 장간, 득지·득생, ΔT, 앱 옵션)
- rules/: UI 설명 레이어(격국/조후 패턴, 라벨, 엔진↔LLM 컨트랙트)
- docs/: 운영 문서(ΔT, tzdb 회귀, 프롬프트, 스토어 정책 등)
- data/: 회귀/민감도/시장비교 데이터셋
- scripts/: 회귀/민감도 스크립트
- ci/: CI 워크플로/설정
- templates/: 보고서/UX 각주/검증 템플릿, evidence_log 샘플

## Engine TODO (by module)
1) resolveLocalToUTC() — IANA tzdb(역사 DST 포함)로 로컬→UTC, 자시 23:00 규칙 반영
2) getMonthBranch() — 절입 테이블(프리컴퓨트) 참조해 월지/계절 산출
3) calcPillars() — 오호둔/오서둔 + 60갑자 매핑
4) mapWangState() — seasons_wang_map.json 적용
5) scoreRootSeal() — zanggan_table.json + root_seal_criteria_v1.json
6) scoreStrength() — strength_criteria_v1.json (월령/통근/투간/합충 보정)
7) buildEvidenceLog() — evidence_log.example.json 필드 준수
8) explain layer — rules/* 로 평가→LLM Polisher/Checker 프롬프트 사용

## Regression & Ops
- tzdb: scripts/tzdb_regress.py + data/tzdb_samples.csv (CI: ci/tzdb-regression.yml)
- ΔT: policy/deltaT_policy_v1.json + scripts/dt_compare_skeleton.py + data/dt_sensitivity_template.csv

## UI/Store
- docs/store_policy_copy_kr.md / en.md — 스토어 표시용
- templates/ux_footnote_template.md — PDF/인쇄 각주

## Notes
- 정책 버전 변경 시 결과가 달라질 수 있으므로, UI에 **rules version**를 항상 노출.
- LLM은 수치 불변. 계산 로직은 코드에서만 수행.
