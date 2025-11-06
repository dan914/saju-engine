# analysis-service

사주 앱 v1.4 프로젝트의 analysis-service FastAPI 서비스입니다.

## Filesystem Requirements
- `policy/` 디렉터리 또는 `POLICY_DIR` 환경 변수를 통해 정책 번들을 제공해야 합니다. 기본 검색 순서는 `policy/`, `saju_codex_*` legacy 번들 순이며, 분석 엔진 초기화 시 모든 정책이 선로드 됩니다.
- `data/terms_*.csv` 집합(또는 동일한 내용을 가리키는 심볼릭 링크)이 필요합니다. 대운 계산과 태세 계산에서 태양 황경표를 조회하므로 서비스 루트(`saju-engine/`) 기준 `data/` 경로가 유효해야 합니다.
- `services/common/` 모듈을 임포트 가능하도록 `PYTHONPATH` 에 루트가 포함되어야 합니다. (도커/WSL 배포 시 `python -m` 형태로 실행하는 것을 권장합니다.)

## Runtime Characteristics
- FastAPI 의 종속성 프로바이더는 싱글톤으로 캐시되어, `AnalysisEngine`/`LLMGuard`/CSV 로더를 한 번만 초기화합니다.
- 애플리케이션 시작 시 `preload_dependencies()` 가 실행되어 정책/데이터를 미리 읽고 검증합니다.
- 종속성은 `services/common/policy_loader.resolve_policy_path()` 를 통해 상대 경로 의존성을 제거했습니다. 따라서 현재 작업 디렉터리와 관계없이 동일하게 동작합니다.

추가 세부 요구사항은 `docs/project_plan_v1.md`와 최상위 README를 참고하세요.
