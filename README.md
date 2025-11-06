# 사주 앱 v1.4 모놀리포 (Codex Skeleton)

이 리포지터리는 사주 앱 v1.4 프로젝트의 기준 구조와 초기 설정을 담고 있습니다. 모든 계산 로직은 KR_classic v1.4 비전 및 불가역 원칙을 따릅니다.

## Security & Performance Status

[![Dependency Audit](https://github.com/{owner}/{repo}/actions/workflows/dependency-audit.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/dependency-audit.yml)
[![Latency Probe](https://github.com/{owner}/{repo}/actions/workflows/latency-probe.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/latency-probe.yml)

**Last Security Scan:** 2025-11-02 | **Status:** ✅ No vulnerabilities | **FastAPI:** 0.120.4 | **Starlette:** 0.49.1

## 디렉터리 개요
- `services/` — 각 백엔드 마이크로서비스(FastAPI 기반) 소스.
- `clients/` — 모바일(Flutter)과 웹(React) 클라이언트 스켈레톤 (개발 예정).
- `rulesets/` — 규칙 JSON 리소스(KR_classic_v1.4 등).
- `data/` — 절기 테이블 등 정적 데이터(예: `terms_1600_2200.csv`).
- `scripts/` — 유틸리티 스크립트(검증, 배치 작업 등).
- `infra/` — 인프라 및 배포 구성(Docker, GitHub Actions 등).
- `docs/` — 아키텍처, 설계, 운영 문서.

## 개발 환경 설정

이 프로젝트는 **모노레포**로 구성되어 있으며, 각 서비스는 독립적인 패키지입니다.

### 초기 설정 (Poetry 1.8.4)

1. **Poetry 1.8.4 설치 (로컬):**
   ```bash
   export POETRY_HOME=$PWD/.poetry-1.8
   python3 scripts/install-poetry.py --version 1.8.4 --yes
   export PATH="$POETRY_HOME/bin:$PATH"
   poetry --version  # 확인: Poetry (version 1.8.4)
   ```

2. **의존성 설치:**
   ```bash
   poetry lock --no-update  # lock 파일 재생성 (1.8.4 호환)
   poetry install --with dev
   ```

   **타이밍:** ~19초 (41개 패키지)

3. **개발 환경 구성 (필수):**
   ```bash
   poetry run python scripts/setup_dev_environment.py
   ```

   이 스크립트는 `.pth` 파일을 생성하여 모든 서비스 디렉토리를 Python 경로에 자동으로 추가합니다.
   이제 `poetry run python`에서 `from app.main import app`이 정상 작동합니다.

### PATH 설정 (영구 적용)

**.bashrc / .zshrc 에 추가:**
```bash
export PATH="/mnt/c/Users/PW1234/.vscode/sajuv2/saju-engine/.poetry-1.8/bin:$PATH"
```

또는 **.envrc (direnv 사용 시):**
```bash
export PATH="$PWD/.poetry-1.8/bin:$PATH"
```

### 테스트 실행

```bash
# 전체 테스트
poetry run pytest

# 특정 서비스 테스트
poetry run pytest services/analysis-service/tests/

# 개별 테스트 파일
poetry run pytest services/analysis-service/tests/test_engine.py -v
```

### 서비스 실행

```bash
# Analysis Service
cd services/analysis-service
poetry run uvicorn app.main:app --reload

# API Gateway
cd services/api-gateway
poetry run uvicorn app.main:app --reload --port 8001
```

### 문제 해결

**ImportError: No module named 'app'**
- 해결: `poetry run python scripts/setup_dev_environment.py` 실행
- 이유: 모노레포 구조에서 서비스들이 Python 경로에 자동으로 추가되지 않음

**테스트 타임아웃**
- pytest.ini에서 timeout=600 (10분) 설정됨
- 개별 테스트: `poetry run pytest -k test_name --timeout=60`

**Poetry 버전**
- 이 프로젝트는 Poetry 1.8.4를 사용합니다
- 다른 버전 사용 시 lock 파일 재생성 필요: `poetry lock --no-update`

## 다음 단계
1. Phase 0 작업 진행: 공통 설정(pyproject, pre-commit, CI 스켈레톤) 추가.
2. 서비스별 FastAPI 스켈레톤 작성 및 공통 콘피그 패키지 정의.
3. 골든셋/규칙 검증 스크립트 구조 확정.

세부 작업 흐름은 `docs/project_plan_v1.md`를 참고하세요.

## 로컬 시크릿 설정 가이드
1. 리포지터리 루트(예: `sajuv2/`)에서 `.env.example` 파일을 `.env`로 복사합니다. 이 파일은 `.gitignore`에 포함되어 있으므로 커밋되지 않습니다.
   ```bash
   cd <repo-root>
   cp .env.example .env
   ```
2. 보안 팀이 회전한 GitHub PAT는 1Password(또는 선정된 임시 비밀 저장소)에 저장됩니다. `grand audit/phase1_rotation_schedule.md`에 링크된 항목을 열어 값을 확인하세요.
3. 로컬에서 `gh auth status`를 실행해 새로운 토큰이 정상적으로 인식되는지 확인합니다.
4. Figma API 키도 동일한 저장소에 보관됩니다. 자동화 도구를 실행할 때는 다음과 같이 환경 변수를 주입하세요.
   ```bash
   FIGMA_API_KEY=$(op item get "S-003 Figma API Key" --fields label=password) \
     npx figma-developer-mcp --help
   ```
5. 비밀을 로컬 파일에 저장해야 한다면 `.env` 하나만 사용하고, 다른 파일(예: `.claude/settings.local.json`)에는 절대 직접 값을 넣지 마세요.

> 회전이 완료되면 `grand audit/phase1_secret_inventory.md`를 업데이트해 완료 시간과 검증 결과를 기록합니다.
