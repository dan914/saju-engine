# Strength Score 정규화 문제 분석 보고서

**Date:** 2025-10-11
**Issue:** YongshinSelector가 신약(-22.0) 사주를 신강으로 잘못 판정
**Severity:** HIGH - 용신 선택에 직접적인 영향

---

## 1. 문제 요약

**현상:**
- 실제 강약 점수: **-22.0 (신약)**
- YongshinSelector 판정: **"strong" (신강)** ❌
- 결과: 용신 선택 로직이 완전히 반대로 작동

**영향:**
- 용신 rationale: "신강 → 식상·관·재 선호" (틀림!)
- 실제로는: "신약 → 인성·비겁 선호" (맞음!)
- 용신 선택 자체는 우연히 맞았지만, 논리가 잘못됨

---

## 2. 근본 원인 (Root Cause)

### 2.1 StrengthEvaluator 점수 범위

**정책 파일:** `saju_codex_batch_all_v2_6_signed/policies/strength_policy_v2.json`

```json
{
  "buckets": {
    "thresholds": {
      "tae_gang": 80,    // 극신강 80~100
      "jung_gang": 65,   // 신강 65~79
      "jung_hwa": 50,    // 중화 50~64
      "jung_yak": 35,    // 신약 35~49
      "tae_yak": 0       // 극신약 0~34
    }
  }
}
```

**실제 구현:**
- 점수 범위: **-무한대 ~ +무한대** (이론적)
- 일반적 범위: **-100 ~ +100**
- 음수 점수 가능 (매우 약한 경우)

**현재 사주 점수:**
- 총점: **-22.0**
- 등급: **신약** (정책상 0~34 범위, -22는 그보다 더 약함)

---

### 2.2 YongshinSelector 기대 범위

**정책 파일:** `policy/yongshin_selector_policy_v1.json`

```json
{
  "strength_binning": {
    "weak": [0.0, 0.4],       // 0% ~ 40%
    "balanced": [0.4, 0.6],   // 40% ~ 60%
    "strong": [0.6, 1.0]      // 60% ~ 100%
  }
}
```

**기대값:**
- 점수 범위: **0.0 ~ 1.0** (비율)
- 예시:
  - 0.3 = 30% = weak (신약)
  - 0.5 = 50% = balanced (중화)
  - 0.8 = 80% = strong (신강)

---

### 2.3 Orchestrator 전달 값

**파일:** `services/analysis-service/app/core/saju_orchestrator.py:349-352`

```python
"strength": {
    "type": strength_result.get("grade_code", "중화"),  # "신약" ✅
    "score": strength_result.get("total", 50)          # -22.0 ❌
}
```

**문제:**
- `strength.score`에 **-22.0**을 그대로 전달
- 정규화 없음!

---

### 2.4 YongshinSelector 처리 로직

**파일:** `services/analysis-service/app/core/yongshin_selector.py:141-149`

```python
def _get_strength_bin(self, score: float) -> str:
    """Map strength score to bin (weak/balanced/strong)."""
    binning = self.policy["strength_binning"]
    if binning["weak"][0] <= score < binning["weak"][1]:
        return "weak"
    elif binning["balanced"][0] <= score < binning["balanced"][1]:
        return "balanced"
    else:
        return "strong"  # ⬅️ 여기로 빠짐!
```

**실행 흐름:**
```
입력: score = -22.0

조건 1: 0.0 <= -22.0 < 0.4?
       → False ❌

조건 2: 0.4 <= -22.0 < 0.6?
       → False ❌

else: return "strong"
       → "strong" 반환 ✅ (잘못됨!)
```

**결과:**
- -22.0이 0.0~1.0 범위 밖
- 모든 조건에서 False
- **else 절로 빠져서 "strong" 반환**

---

## 3. 영향 분석

### 3.1 용신 선택에 미친 영향

**잘못된 판정:**
```python
BIN: strong  # ❌ 실제로는 weak
```

**잘못된 Base Preferences:**
```python
# "strong" 사주의 선호도 (틀림!)
"BASE:output→화",     # 식상 (我生)
"BASE:official→금",   # 관살 (克我)
"BASE:wealth→토"      # 재성 (我克)
```

**실제로 적용되어야 할 선호도:**
```python
# "weak" 사주의 선호도 (맞음!)
"BASE:resource→수",    # 인성 (生我)
"BASE:companion→목"    # 비겁 (同我)
```

### 3.2 Rationale 오류

**출력된 rationale:**
```python
[
  "신강 → 식상·관·재 선호",  # ❌ 틀림!
  "충(沖) 강함 → 완충 필요",
  "금 과다 억제 필요"
]
```

**올바른 rationale:**
```python
[
  "신약 → 인성·비겁 선호",  # ✅ 맞음!
  "충(沖) 강함 → 완충 필요",
  "금 과다 억제 필요"
]
```

### 3.3 최종 용신 점수

**현재 점수:**
```
화 (Fire):  +0.22
토 (Earth): +0.19
수 (Water): +0.07
목 (Wood):  -0.08
금 (Metal): -0.08
```

**분석:**
- Distribution bias (DIST:deficit/excess)가 주도적 역할
- Base preferences는 잘못 적용되었지만
- Distribution bias가 화·토를 끌어올림 (부족한 원소)
- **우연히 결과는 맞게 나왔지만, 논리는 틀렸음!**

---

## 4. 해결 방안

### 방안 1: Orchestrator에서 정규화 (권장 ✅)

**위치:** `services/analysis-service/app/core/saju_orchestrator.py:346-352`

**현재 코드:**
```python
input_data = {
    "strength": {
        "type": strength_result.get("grade_code", "중화"),
        "score": strength_result.get("total", 50)  # ❌ 그대로 전달
    }
}
```

**수정 코드:**
```python
def _normalize_strength_score(self, score: float) -> float:
    """
    Normalize strength score from StrengthEvaluator range to 0.0-1.0

    StrengthEvaluator range: -100 ~ +100 (typical)
    YongshinSelector range: 0.0 ~ 1.0

    Mapping:
    -100 → 0.0 (극신약)
      0  → 0.5 (중화)
    +100 → 1.0 (극신강)
    """
    # Clamp to expected range
    clamped = max(-100, min(100, score))

    # Linear normalization: [-100, 100] → [0.0, 1.0]
    normalized = (clamped + 100) / 200.0

    return normalized

# Usage:
input_data = {
    "strength": {
        "type": strength_result.get("grade_code", "중화"),
        "score": self._normalize_strength_score(strength_result.get("total", 50))
    }
}
```

**예시:**
```python
-22.0 → ((-22.0 + 100) / 200) = 78 / 200 = 0.39
0.39는 [0.0, 0.4] 범위 → "weak" ✅
```

---

### 방안 2: YongshinSelector에서 자동 정규화

**위치:** `services/analysis-service/app/core/yongshin_selector.py:141-149`

**수정 코드:**
```python
def _get_strength_bin(self, score: float) -> str:
    """Map strength score to bin (weak/balanced/strong)."""
    binning = self.policy["strength_binning"]

    # Auto-normalize if score is outside 0.0-1.0 range
    if score < 0.0 or score > 1.0:
        # Assume StrengthEvaluator range [-100, 100]
        normalized = (max(-100, min(100, score)) + 100) / 200.0
    else:
        normalized = score

    if binning["weak"][0] <= normalized < binning["weak"][1]:
        return "weak"
    elif binning["balanced"][0] <= normalized < binning["balanced"][1]:
        return "balanced"
    else:
        return "strong"
```

**장점:**
- YongshinSelector가 독립적으로 작동
- 다른 orchestrator에서도 사용 가능

**단점:**
- YongshinSelector가 StrengthEvaluator의 범위를 알아야 함 (coupling)
- 명시적이지 않음

---

### 방안 3: 정책 파일 범위 확장 (비권장 ❌)

**정책 파일:** `policy/yongshin_selector_policy_v1.json`

**수정:**
```json
{
  "strength_binning": {
    "weak": [-100, 40],
    "balanced": [40, 60],
    "strong": [60, 100]
  }
}
```

**단점:**
- 정책 파일이 0.0~1.0 비율 개념을 버림
- 다른 엔진과의 일관성 깨짐
- 비권장!

---

## 5. 권장 해결책

**방안 1 (Orchestrator 정규화)** 을 권장합니다.

**이유:**
1. **명시적:** orchestrator가 변환 책임을 명확히 가짐
2. **분리:** 각 엔진이 독립적으로 작동
3. **일관성:** 모든 엔진이 0.0~1.0 정규화된 값을 받음
4. **테스트 용이:** 정규화 로직을 독립적으로 테스트 가능

---

## 6. 구현 예시

### 6.1 정규화 함수 추가

**파일:** `services/analysis-service/app/core/saju_orchestrator.py`

```python
def _normalize_strength_score(self, score: float) -> float:
    """
    Normalize strength score to 0.0-1.0 range.

    Args:
        score: Raw strength score from StrengthEvaluator (-100 ~ +100)

    Returns:
        Normalized score (0.0 ~ 1.0)

    Examples:
        -100 → 0.0 (극신약)
        -22  → 0.39 (신약)
        0    → 0.5 (중화)
        50   → 0.75 (신강)
        100  → 1.0 (극신강)
    """
    # Clamp to expected range
    clamped = max(-100, min(100, score))

    # Linear mapping: [-100, 100] → [0.0, 1.0]
    normalized = (clamped + 100) / 200.0

    return normalized
```

### 6.2 _call_yongshin 수정

**파일:** `services/analysis-service/app/core/saju_orchestrator.py:346-370`

**Before:**
```python
input_data = {
    "strength": {
        "type": strength_result.get("grade_code", "중화"),
        "score": strength_result.get("total", 50)
    }
}
```

**After:**
```python
input_data = {
    "strength": {
        "type": strength_result.get("grade_code", "중화"),
        "score": self._normalize_strength_score(
            strength_result.get("total", 50)
        )
    }
}
```

### 6.3 테스트 케이스

```python
def test_normalize_strength_score():
    orchestrator = SajuOrchestrator()

    # Test cases
    assert orchestrator._normalize_strength_score(-100) == 0.0   # 극신약
    assert orchestrator._normalize_strength_score(-22) == 0.39   # 신약
    assert orchestrator._normalize_strength_score(0) == 0.5      # 중화
    assert orchestrator._normalize_strength_score(50) == 0.75    # 신강
    assert orchestrator._normalize_strength_score(100) == 1.0    # 극신강

    # Edge cases
    assert orchestrator._normalize_strength_score(-200) == 0.0   # Clamp
    assert orchestrator._normalize_strength_score(200) == 1.0    # Clamp
```

---

## 7. 검증 방법

수정 후 다음 결과를 기대:

**입력:**
- strength.score: -22.0 (raw)

**정규화 후:**
- strength.score: 0.39 (normalized)

**YongshinSelector 판정:**
```python
0.0 <= 0.39 < 0.4  → True ✅
return "weak"
```

**Rationale:**
```python
[
  "신약 → 인성·비겁 선호",  # ✅ 올바름!
  "충(沖) 강함 → 완충 필요",
  "금 과다 억제 필요"
]
```

**Base Preferences:**
```python
"BASE:resource→수",    # 인성 (生我) ✅
"BASE:companion→목"    # 비겁 (同我) ✅
```

---

## 8. 추가 고려 사항

### 8.1 다른 엔진도 영향 받는가?

**확인 필요:**
- ClimateAdvice 엔진
- LuckFlow 엔진
- GyeokgukClassifier 엔진
- PatternProfiler 엔진

모두 strength 점수를 사용하는지 확인하고, 필요 시 정규화 적용.

### 8.2 정책 파일 문서화

`policy/yongshin_selector_policy_v1.json`에 다음 주석 추가:

```json
{
  "strength_binning": {
    "_comment": "Normalized strength score range (0.0~1.0). Orchestrator must normalize StrengthEvaluator output (-100~+100) before passing.",
    "weak": [0.0, 0.4],
    "balanced": [0.4, 0.6],
    "strong": [0.6, 1.0]
  }
}
```

---

## 9. 타임라인

**우선순위:** HIGH
**난이도:** LOW (간단한 정규화 로직)
**예상 시간:** 30분

**작업 순서:**
1. ✅ 문제 분석 완료 (현재)
2. ⏳ _normalize_strength_score() 함수 추가
3. ⏳ _call_yongshin() 수정
4. ⏳ 테스트 실행
5. ⏳ 리포트 재생성

---

**Report by:** Claude Code
**Date:** 2025-10-11 KST
**Status:** ANALYSIS COMPLETE - Ready for implementation
