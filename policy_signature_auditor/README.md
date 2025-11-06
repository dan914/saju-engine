# Policy Signature Auditor v1.0

**RFC-8785 스타일 정책 서명 및 검증 시스템**

## 개요

정책/스키마/테스트 JSON 파일을 JCS(JSON Canonicalization Scheme) 스타일로 정규화하고 SHA-256 해시를 계산하여:

- **sign**: 해시를 `policy_signature` 필드에 주입 (in-place 또는 sidecar)
- **verify**: 파일 내 서명과 재계산 해시 일치 여부 확인
- **diff**: 서명 제외 정규화 결과 비교 (구조 변조 탐지)

해시 계산 시 `policy_signature` 필드는 빈 문자열(`""`)로 간주하여 정규화합니다.

## 포함물 (폴더 트리)

```
policy_signature_auditor/
├── psa_cli.py                  # CLI 엔트리포인트
├── auditor.py                  # sign/verify/diff 로직
├── jcs.py                      # JCS (RFC-8785 유사) 정규화
├── schemas/
│   └── policy_meta.schema.json # 엄격 모드 검사용 최소 스키마
├── tests/
│   ├── data/
│   │   └── sample_policy.json  # 샘플 정책 (UNSIGNED)
│   └── test_sign_verify.py     # 동작 검증 스크립트
└── README.md                   # 본 문서
```

## 빠른 시작

**요구사항**: Python 3.9+ (외부 의존성 없음)

### 1) 서명 (in-place 주입)

```bash
python policy_signature_auditor/psa_cli.py sign policy/llm_guard_policy_v1.json --in-place --strict
```

### 2) 서명 검증 (일괄)

```bash
python policy_signature_auditor/psa_cli.py verify "policy/**/*.json" --strict
```

### 3) 캐노니컬 비교 (서명 제외)

```bash
python policy_signature_auditor/psa_cli.py diff policy/a.json policy/b.json
```

## CLI 옵션

### sign 명령

- `--in-place`: 파일 안의 `policy_signature`를 갱신해 저장
- `--write-sidecar`: `<file>.sha256` 별도 파일로 해시 저장
- `--strict`: 최상위 메타 필드 검증 (policy_version, policy_date, ko_labels, dependencies)

### verify 명령

- `--strict`: 메타 필드 검증

### diff 명령

- `--verbose`, `-v`: 캐노니컬 형식 출력

## 종료 코드

- `0`: 성공
- `1`: 검증 실패 (Mismatch)
- `2`: 에러 (파일 없음, 잘못된 JSON 등)

## JCS (정규화) 구현 요약

본 구현은 실무형 JCS로, RFC-8785와 호환 가능:

1. **객체 키**: 유니코드 코드포인트 순 정렬
2. **문자열**: `\`, `"`, 제어문자 → `\uXXXX` 이스케이프
3. **숫자**:
   - `-0` → `0`
   - 지수 사용 범위 기준 정규화
   - 소수부 뒤 영(0) 제거
   - 지수 표기 시 `e`(소문자), `+` 금지
4. **불리언/널**: `true`/`false`/`null`
5. **UTF-8 바이트로 직렬화** 후 SHA-256

## 테스트 실행

```bash
python policy_signature_auditor/tests/test_sign_verify.py
```

**예상 출력**:
```
============================================================
Policy Signature Auditor - Test Suite
============================================================
Test 1: Sign and verify...
   ✅ Signed with hash: 3a7bd3e2360a3d29...
   ✅ Verified successfully

Test 2: Detect tampering...
   ✅ Original signature: 3a7bd3e2360a3d29...
   ✅ Tampering detected (hash mismatch)

Test 3: Diff policies...
   ✅ Policies are structurally equal (signatures ignored)
   ✅ Content difference detected

Test 4: Strict mode validation...
   ✅ Missing field detected: Missing required field in strict mode: policy_date
   ✅ Invalid ko_labels detected: ko_labels must be true in strict mode

Test 5: File operations...
   ✅ File signed: 5f3c8d2a...
   ✅ File verified

============================================================
✅ All tests passed!
============================================================
```

## CI/운영 통합 가이드

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
python policy_signature_auditor/psa_cli.py verify "policy/**/*.json" "schema/**/*.json" --strict
```

### PR/CI 검증

```bash
python policy_signature_auditor/psa_cli.py verify "policy/**/*.json" --strict || exit 1
```

### 릴리스

```bash
# 모든 정책 파일 서명
python policy_signature_auditor/psa_cli.py sign "policy/**/*.json" --in-place --strict

# 릴리스 노트에 해시 기록 권장
```

### 런타임 로더

정책 로딩 시:

```python
from policy_signature_auditor.auditor import verify_policy

# 정책 로드
with open("policy/my_policy.json") as f:
    policy = json.load(f)

# 검증
is_valid, expected, actual = verify_policy(policy, strict=True)

if not is_valid:
    # 로드 거부 & 이전 버전 폴백
    logger.error(f"Policy signature mismatch: expected={expected}, actual={actual}")
    raise PolicyIntegrityError("Policy file has been tampered with")
```

## 왜 지금 이게 최선인가

1. **프롬프트 불필요**: 정책 파일 생성은 사람/LLM 모두 가능하지만, 신뢰성 확보는 코드 서명이 필수
2. **재현성**: OS/로케일 무관하게 동일 해시 (키 정렬·숫자 표준화·공백 제거)
3. **확장성**: `jcs.py`만 표준 라이브러리로 교체하면 RFC-8785 완전 준수 가능
4. **검증 가능성**: 감사 추적, 변조 탐지, 버전 무결성 보장

## 라이선스

MIT License (프로젝트 라이선스와 동일)

## 버전 관리

- **v1.0.0** (2025-10-09): 초기 릴리스
  - JCS 정규화 구현
  - sign/verify/diff 명령
  - 엄격 모드 메타데이터 검증
  - 테스트 스위트 포함

## 지원 및 문의

GitHub Issues: [your-repo]/issues
