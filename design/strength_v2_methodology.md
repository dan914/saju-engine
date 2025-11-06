# 강약 평가기 v2(StrengthEvaluator v2) Methodology — v2.0.1 Patch Notes

본 문서는 v2.0 → v2.0.1 패치에서의 구조 개선 사항을 요약합니다. 계산식(得令/得地/得時/得勢) 자체는 v2.0과 동일합니다.

## 1) CI 가중치 합 검증 추가

**변경**: 정책에 `ci_checks.assertions`를 도입하여
`weights.deukryeong + deukji + deuksi + deukse == 100`을 빌드 단계에서 강제(`on_fail: "fail_build"`).

**영향**: 스키마 수준 제약을 보완, 파이프라인에서 즉시 실패 처리.

## 2) relation_policy 적용 스위치 분리

**변경 전**: `dependencies.relation_policy.apply` (혼동 여지)
**변경 후**: `dependencies.relation_policy`는 참조 메타데이터만 보유하고,
실제 적용 여부는 상위 `options.relation_policy.apply`에서 제어.

**의도**: 정책 의존성과 실행 플래그를 분리해 오해 방지.

## 3) hidden_weights 참조 구조 개선

**변경**: 상위에 `common_hidden_weights`를 신설하고,
- `deukji.hidden_weights_ref: "#/common_hidden_weights"`
- `deuksi.hidden_weights_ref: "#/common_hidden_weights"`
로 통일(하드코딩 경로 대신 JSON Pointer).

**스키마**: `deukji`는 `oneOf(hidden_weights | hidden_weights_ref)`를 허용하여 하위 호환.

**가드**: `ci_checks.assertions`에 `json_pointer_exists('#/common_hidden_weights')` 추가.

---

## 참고: 계산 로직(요약)

得令/得地/得時/得勢 공식과 파라미터는 v2.0과 동일(정책 본문 참조).
라벨링은 raw 점수 기준 후 소수 반올림(경계 점프 방지).

**엔진명(ko)**: 강약 평가기 v2 · 정책 버전: 2.0.1
