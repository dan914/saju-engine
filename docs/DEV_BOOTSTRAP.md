# 개발 환경 부트스트랩 가이드 (사주 앱 v1.4)

## 1. 기본 요구 사항
- Python 3.11.x
- Node.js 20.x (웹 클라이언트)
- Flutter 3.x (모바일 클라이언트)
- Docker 24.x 이상 (선택: 로컬 인프라 실행)

## 2. 가상환경 생성
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

## 3. 공통 도구 설치
```bash
pip install -e .[dev]
pre-commit install
```

> 참고: macOS 샌드박스 환경에서는 `python3 -m compileall` 실행 시 캐시 디렉터리 권한 문제가 발생할 수 있습니다. 필요 시 `export PYTHONPYCACHEPREFIX=$(pwd)/.pycache` 후 재실행하세요.

## 4. API Gateway 스켈레톤 실행
```bash
cd services/api-gateway
uvicorn app.main:app --reload
```

헬스체크:
```bash
curl http://127.0.0.1:8000/health
```

## 5. 테스트
```bash
pytest services/api-gateway
pytest services/astro-service
pytest services/tz-time-service
pytest services/pillars-service
pytest services/analysis-service
pytest services/llm-polish
pytest services/llm-checker
```

- 필요한 경우 개별 서비스 디렉터리에서 `pip install -e .[test]`로 선택적 의존성을 설치할 수 있습니다.
- 골든셋/규칙 검증 러너 등 추가 테스트는 Phase 2 이후 `docs/project_plan_v1.md`를 업데이트하며 확장합니다.

## 6. 다음 작업 제안
1. Phase 0 나머지 작업: 각 서비스용 패키지 구조 결정, 공통 라이브러리 패키지 초안 작성.
2. Phase 1 선행 조사: Astronomy Engine, tzdb 핸들링 라이브러리 후보 정리.
3. CI 스켈레톤 추가: GitHub Actions 워크플로(포맷/테스트) 초안.

## 7. 공통 코드 구조
- `services/common` 패키지에서 FastAPI 서비스 공통 요소(예: `create_service_app`)를 제공합니다.
- 루트에서 `pip install -e .[dev]`를 실행하면 `services.common`이 즉시 임포트 가능해집니다.
- 각 서비스의 `app/main.py`는 공통 팩토리를 사용하여 `/health`, `/` 기본 엔드포인트를 자동 등록합니다.

## 8. CI 파이프라인 요약
- `.github/workflows/ci.yml` 워크플로가 lint(black/isort/ruff)와 각 서비스별 pytest를 실행합니다.
- 로컬에서도 `black --check .`, `isort --check-only .`, `ruff check .`, `pytest services/<service>`로 동일한 검사를 재현할 수 있습니다.
- 새 서비스를 추가할 때는 동일한 패턴으로 테스트를 등록하여 품질 게이트를 유지하십시오.
## 9. Trace 메타데이터 활용
- `services.common.TraceMetadata`를 사용해 서비스 간 trace 필드 구조를 통일합니다.
- 각 서비스는 `.to_dict()` 결과를 Pydantic 모델(또는 응답 dict)에 주입하여 `rule_id`, `tz`, `flags` 등을 일관되게 반환합니다.
- 새로운 플래그나 필드를 추가할 때는 TraceMetadata를 확장하고 관련 테스트를 업데이트하세요.
- Pillars 서비스는 `app/core/resolve.py`와 `app/core/month.py`를 통해 시간 변환 및 월지 판정을 수행하며, 테스트(`tests/test_resolve.py`, `tests/test_month_branch.py`)로 검증됩니다.
- 4주 계산은 `app/core/pillars.py`와 `app/core/engine.py`에서 수행되며, 60갑자/오호둔/오서둔 로직을 포함합니다.
- 강약 계산은 `app/core/wang.py`와 `app/core/strength.py`를 통해 계절/근/가시 천간 점수를 산출합니다.
- 근거 로그는 `app/core/evidence.py`에서 생성되며, 엔진 trace의 `evidence` 필드로 포함됩니다.
- 관계 변환은 `analysis-service/app/core/relations.py`에서 addendum v2 정책을 사용합니다.
- 격국 판별 프로토타입은 `analysis-service/app/core/structure.py`에 있습니다.
- 기후 평가는 `analysis-service/app/core/climate.py`를 통해 기후 편향을 계산합니다.
- 왕상판정은 `policies/seasons_wang_map_v2.json`을 사용합니다.
- 강약 스케일 조정은 `policies/strength_scale_v1_1.json` 기반입니다.
- 근거 로그는 `policies/boundary_review_policy_v1.json`, `policies/lunar_policy_v1.json` 등의 신규 필드를 포함합니다.
- 운 계산은 `analysis-service/app/core/luck.py`에서 luck_policy_v1.json을 따릅니다.
- 신살 목록은 `ShenshaCatalog`를 통해 정책 기반으로 제공됩니다.
- 텍스트 필터는 `analysis-service/app/core/text_guard.py`에서 text_guard_policy_v1.json을 참조합니다.
- 용신 추천 가드는 `analysis-service/app/core/recommendation.py`가 recommendation_policy_v1.json을 사용합니다.
- 윤달/경계 정책은 `policies/lunar_policy_v1.json`, `policies/boundary_review_policy_v1.json`을 참조합니다.
- 오합 및 JDN 정밀도 정책은 각각 `policies/five_he_policy_v1.json`, `policies/jdn_precision_policy_v1.json`에 정의되어 있습니다.
- STD vs LMT 검증 테스트(`tests/test_std_vs_lmt.py`)로 time_basis=STD만 사용되는지 회귀 검증합니다.
- Telemetry: evidence에서 LMT.applied==true 발생 시 알림하도록 모니터링 지표를 추가하세요.
- ΔT 정책 파서는 `services/astro-service/app/core/delta_t.py`에서 `deltaT_policy_v1.json`을 해석합니다.
- `scripts/dt_compare.py`는 정책 임계값으로 ΔT 비교 경고를 산출합니다.
- 여기에/재성 승격은 `policies/root_seal_policy_v2_3.json`과 `policies/yugi_policy_v1_1.json`을 따릅니다.
