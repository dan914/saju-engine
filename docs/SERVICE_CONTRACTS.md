# 핵심 서비스 계약 개요 (v0.1 스켈레톤)

본 문서는 사주 앱 v1.4 백엔드 서비스의 REST 계약을 정의하기 위한 토대를 제공합니다. 실제 구현 시 KR_classic v1.4 규칙과 비전 문서를 기준으로 세부 필드를 확정해야 합니다.

## 1. astro-service
- 베이스 경로: `/v2`
- 주요 책임: 24절기(λ⊙), ΔT, 절입 UTC/Local 시각 제공. 프리로드된 `terms_1600_2200.csv` 기반.

### 1.1 POST `/v2/terms`
- 설명: 요청한 연도와 타임존에 대한 24절기 정보를 반환.
- 요청 바디:
  ```json
  {
    "year": 1992,
    "timezone": "Asia/Seoul"
  }
  ```
- 응답 예시(요약):
  ```json
  {
    "year": 1992,
    "timezone": "Asia/Seoul",
    "terms": [
      {
        "term": "立春",
        "lambda_deg": 315.0,
        "utc_time": "1992-02-04T06:17:00Z",
        "local_time": "1992-02-04T15:17:00+09:00",
        "delta_t_seconds": 57.4,
        "source": "AstronomyEngine",
        "algo_version": "AE-2.3+EM"
      }
    ],
    "trace": {
      "rule_id": "KR_classic_v1.4",
      "deltaTSeconds": 57.4,
      "tz": {"iana": "Asia/Seoul", "event": "none", "tzdbVersion": "2025a"}
    }
  }
  ```
- TODO: 절기 테이블 로더, 타임존 변환, trace flags(`edge`, `tzTransition`, `deltaT>5s`) 구현.

## 2. tz-time-service
- 베이스 경로: `/v2`
- 주요 책임: IANA tzdb 기반 UTC↔지역시 변환, 역사 이벤트 감지, tzdb 버전 모니터링.

### 2.1 POST `/v2/time/convert`
- 설명: 주어진 시각을 source→target 타임존으로 변환하고 관련 이벤트를 리턴.
- 요청 바디:
  ```json
  {
    "instant": "1992-07-15T14:40:00Z",
    "source_tz": "UTC",
    "target_tz": "Asia/Seoul"
  }
  ```
- 응답 예시(초안):
  ```json
  {
    "input": {
      "instant": "1992-07-15T14:40:00Z",
      "source_tz": "UTC",
      "target_tz": "Asia/Seoul"
    },
    "converted": "1992-07-15T23:40:00+09:00",
    "tzdb_version": "2025a",
    "events": [
      {
        "iana": "Asia/Seoul",
        "kind": "transition",
        "effective_from": "1988-05-07T16:00:00Z",
        "notes": "1987–1988 DST window"
      }
    ],
    "trace": {
      "rule_id": "KR_classic_v1.4",
      "tz": {"source": "UTC", "target": "Asia/Seoul", "tzdbVersion": "2025a"},
      "flags": {"tzTransition": true}
    }
  }
  ```
- TODO: tz 전환 윈도 감시(±48h), Pyongyang +08:30(2015–2018) 이벤트 반영, 감시 Job.


## 3. pillars-service
- 베이스 경로: `/v2`
- 책임: KR_classic v1.4 규칙에 따라 연/월/일/시주 계산, trace 메타데이터 반환.

### 3.1 POST `/v2/pillars/compute`
- 설명: 사용자 입력(localDateTime, timezone, rules)에 대한 4주 결과를 결정론적으로 반환.
- 요청 바디 예시:
  ```json
  {
    "localDateTime": "1992-07-15T23:40:00",
    "timezone": "Asia/Seoul",
    "rules": "KR_classic_v1.4"
  }
  ```
- 응답 예시(스켈레톤):
  ```json
  {
    "pillars": {
      "year": {"pillar": "壬申", "boundaryUTC": "1992-02-04T06:17:00Z", "term": "立春"},
      "month": {"pillar": "辛未", "boundaryUTC": "1992-07-06T15:00:00Z", "term": "小暑"},
      "day": {"pillar": "丁丑", "dayStartLocal": "1992-07-15T23:00:00+09:00", "policy": "zi-start-23"},
      "hour": {"pillar": "庚子", "rangeLocal": ["23:00:00", "01:00:00"], "rule": "五鼠遁"}
    },
    "trace": {
      "rule_id": "KR_classic_v1.4",
      "deltaTSeconds": 57.4,
      "tz": {"iana": "Asia/Seoul", "event": "none", "tzdbVersion": "2025a"},
      "astro": {"primary": "AstronomyEngine", "diffSeconds": 0.0},
      "boundaryPolicy": "LCRO",
      "epsilonSeconds": 0.001,
      "flags": {"edge": false, "tzTransition": false, "deltaT>5s": false}
    }
  }
  ```
- TODO: 입춘 315°, 절입, 오호둔/오서둔 테이블, ΔT 보정, tz 이벤트 플래그를 실제 값으로 계산.


## 4. analysis-service
- 베이스 경로: `/v2`
- 책임: 십신/관계/강약 분석, trace(rule_id 등) 유지.

### 4.1 POST `/v2/analyze`
- 설명: pillars-service 결과를 입력받아 십신, 관계, 강약 평가를 제공.
- 요청 바디 예시:
  ```json
  {
    "pillars": {
      "year": {"pillar": "壬申"},
      "month": {"pillar": "辛未"},
      "day": {"pillar": "丁丑"},
      "hour": {"pillar": "庚子"}
    },
    "options": {"include_trace": true}
  }
  ```
- 응답 예시(스켈레톤):
  ```json
  {
    "ten_gods": {
      "summary": {
        "year": "偏印",
        "month": "正財",
        "day": "日主",
        "hour": "食神"
      }
    },
    "relations": {
      "he6": [["子", "丑"]],
      "sanhe": [["申", "子", "辰"]],
      "chong": [["子", "午"]],
      "hai": [["子", "未"]],
      "po": [["子", "卯"]],
      "xing": [["寅", "巳", "申"]]
    },
    "strength": {
      "level": "중강",
      "basis": {
        "season": "得令",
        "roots": "有本氣",
        "seal": "天干1見",
        "peer": "同氣"
      }
    },
    "trace": {
      "rule_id": "KR_classic_v1.4",
      "notes": "placeholder analysis pending rules integration"
    }
  }
  ```
- TODO: rulesets 기반 십신 매핑, 관계 도출, 강약 점수화 로직을 실제 구현하고 trace 확장.


## 3. 공통 리소스
- `services/common.create_service_app`: FastAPI 앱 메타데이터(`/`, `/health`) 노출.
- 향후 공유 모듈 계획: 로깅/트레이싱, 규칙 로더(`rulesets/`), 오류 규약.

## 4. 공통 Trace / Error 스키마 초안
### 4.1 Trace 객체
```json
{
  "rule_id": "KR_classic_v1.4",
  "deltaTSeconds": 57.4,
  "tz": {
    "iana": "Asia/Seoul",
    "event": "DST",
    "tzdbVersion": "2025a"
  },
  "boundaryPolicy": "LCRO",
  "epsilonSeconds": 0.001,
  "flags": {
    "edge": false,
    "tzTransition": false,
    "deltaT>5s": false
  }
}
```
- 모든 서비스는 trace 객체를 일관된 키로 포함해야 하며, 값은 규칙 검증 스크립트와 동기화한다.
- tz-time-service는 `tz` 객체 확장을 통해 정책 이벤트(예: Pyongyang +08:30) 표시.

### 4.2 오류 응답 포맷
```json
{
  "error": {
    "code": "DATA_NOT_FOUND",
    "message": "Solar term table missing for 1991",
    "details": {
      "resource": "terms_1991.csv"
    }
  },
  "trace": {"requestId": "..."}
}
```
- `code`는 명시적 열거형으로 관리하고, LLM 레이어에는 그대로 전달하지 않는다.
- `trace.requestId`는 로깅/관측과 연동한다.

## 5. 추후 문서화 항목
1. `/v2/pillars/compute`, `/v2/analyze`, `/v2/transit/*` 상세 계약.
2. Trace 오브젝트 키/값 확정 및 서비스별 필수 필드 목록.
3. LLM 레이어 인터페이스(Polisher/Checker) 및 수치 불변 검증 절차.

> 본 문서는 추후 Phase 1~3 진행에 맞춰 구체화해야 하며, 실제 값/필드명은 규칙 검증 스크립트와 동기화해야 합니다.
