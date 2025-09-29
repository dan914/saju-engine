# 사주 앱 v1.4 모놀리포 (Codex Skeleton)

이 리포지터리는 사주 앱 v1.4 프로젝트의 기준 구조와 초기 설정을 담고 있습니다. 모든 계산 로직은 KR_classic v1.4 비전 및 불가역 원칙을 따릅니다.

## 디렉터리 개요
- `services/` — 각 백엔드 마이크로서비스(FastAPI 기반) 소스.
- `clients/` — 모바일(Flutter)과 웹(React) 클라이언트 코드.
- `rulesets/` — 규칙 JSON 리소스(KR_classic_v1.4 등).
- `data/` — 절기 테이블 등 정적 데이터(예: `terms_1600_2200.csv`).
- `scripts/` — 유틸리티 스크립트(검증, 배치 작업 등).
- `infra/` — 인프라 및 배포 구성(Docker, GitHub Actions 등).
- `docs/` — 아키텍처, 설계, 운영 문서.

## 다음 단계
1. Phase 0 작업 진행: 공통 설정(pyproject, pre-commit, CI 스켈레톤) 추가.
2. 서비스별 FastAPI 스켈레톤 작성 및 공통 콘피그 패키지 정의.
3. 골든셋/규칙 검증 스크립트 구조 확정.

세부 작업 흐름은 `docs/project_plan_v1.md`를 참고하세요.
