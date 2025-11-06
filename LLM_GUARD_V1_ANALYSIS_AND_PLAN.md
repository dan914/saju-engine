# LLM Guard v1.0 분석 및 구현 계획

**작성일**: 2025-10-06
**분석 방식**: Ultrathink Deep Analysis
**상태**: 📋 계획 수립 완료, 구현 대기

---

## 📊 Executive Summary

**현재 상태**: 기본적인 텍스트 필터링 수준 (10% 커버리지)
**목표 상태**: 본격적인 LLM Guard v1.0 시스템 (100% 정책 준수)
**예상 작업량**: 8-12일 (1,500-2,000줄 코드)
**복잡도**: ⚠️ **HIGH** - 완전히 새로운 아키텍처 필요

---

## 1. 현재 상태 분석 (As-Is)

### 1.1 현재 LLMGuard 구조

```python
@dataclass(slots=True)
class LLMGuard:
    text_guard: TextGuard                    # 금지 용어 → ●● 치환
    recommendation_guard: RecommendationGuard # structure 유무 체크
    korean_enricher: KoreanLabelEnricher     # 한국어 라벨 추가 (신규)

    def prepare_payload(self, response: AnalysisResponse) -> dict:
        # 1. 검증
        # 2. dict 변환
        # 3. 한국어 라벨 추가
        return enriched

    def postprocess(self, original, llm_payload, ...) -> AnalysisResponse:
        # 1. 스키마 검증
        # 2. trace 불변성 체크
        # 3. 텍스트 필터링 (금지어)
        # 4. 추천 결정
        return candidate
```

### 1.2 TextGuard (매우 단순)

```python
class TextGuard:
    forbidden_terms: List[str]    # ["욕설", "비속어", ...]

    def guard(self, text: str, topic_tags: Iterable[str]) -> str:
        for term in self.forbidden_terms:
            text = text.replace(term, "●●")
        # 특정 토픽에 면책 문구 추가
        return text
```

**한계**:
- ❌ 규칙 기반 체크 없음
- ❌ Severity 없음
- ❌ Verdict (allow/deny/revise) 없음
- ❌ 패치 제안 없음

### 1.3 RecommendationGuard (매우 단순)

```python
class RecommendationGuard:
    def decide(self, *, structure_primary: str | None) -> Dict:
        if self.require_structure and not structure_primary:
            return {"enabled": False, "action": "suppress"}
        return {"enabled": True, "action": "allow"}
```

**한계**:
- ❌ 단순 boolean 로직
- ❌ 정책 기반 결정 없음

### 1.4 KoreanLabelEnricher (신규, 방금 구현)

```python
class KoreanLabelEnricher:
    def enrich(self, payload: Dict) -> Dict:
        # 141개 한국어 매핑 적용
        # *_ko 필드 추가
        return enriched
```

**장점**:
- ✅ 141개 매핑 완비
- ✅ 전문가 검증 완료
- ✅ 21개 테스트 통과

**한계**:
- ❌ 필수 검증 없음 (누락 시 에러 없이 원본 반환)
- ❌ KO-first 규칙 강제 없음

---

## 2. 요구사항 분석 (To-Be)

### 2.1 LLM Guard v1.0 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Guard v1.0                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pre-Gen Hook (사전 검증)                                   │
│  ├─ DETERMINISM (DT-001~003): 버전/서명/해시 검증           │
│  ├─ TRACE_INTEGRITY (TR-001~002): trace 무결성             │
│  ├─ EVIDENCE_BOUND (EV-001): evidence 필수 체크            │
│  └─ KO_FIRST_LABELS (KO-001): label_ko 필수 체크           │
│                                                             │
│  ↓ [LLM Polisher] ← Evidence + Policy 전달                 │
│                                                             │
│  Post-Gen Hook (사후 검증)                                  │
│  ├─ EVIDENCE_BOUND (EV-002~003): 외부 사실/추정 금지       │
│  ├─ POLICY_BOUND (PO-001~002): 비정책 용어 금지            │
│  ├─ KO_FIRST_LABELS (KO-002~003): EN-only/톤 위반 감지     │
│  └─ HARM_GUARD (HG-001~003): 의료/법률/재무 단정 금지      │
│                                                             │
│  Decision Engine                                           │
│  ├─ Aggregation: max(severity) → verdict                  │
│  ├─ Decision Ladder: deny > revise > allow                │
│  └─ Patch Generator: revise 시 수정 제안                   │
│                                                             │
│  Output                                                    │
│  └─ GuardResult {checks[], decision, meta}                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Rule Families (6개)

#### 1️⃣ DETERMINISM (DT-001~003) - Phase: pre
- **DT-001**: 정책 버전 불일치 → **deny**
- **DT-002**: 정책/증거 서명 미검증 → **deny**
- **DT-003**: 입력 해시 누락 → **revise**

#### 2️⃣ TRACE_INTEGRITY (TR-001~002) - Phase: pre
- **TR-001**: trace 항목 누락 (component/policy_rule_id) → **revise**
- **TR-002**: 정책-룰ID 매핑 불일치 → **revise**

#### 3️⃣ EVIDENCE_BOUND (EV-001~003) - Phase: both
- **EV-001**: 증거 미제공 추론 금지 → **deny**
- **EV-002**: 외부 사실 인용 금지 (뉴스/블로그 등) → **revise**
- **EV-003**: LLM 자유 추정 금지 (느낌/직감 등) → **revise**

#### 4️⃣ POLICY_BOUND (PO-001~002) - Phase: post
- **PO-001**: 비정책 용어 사용 금지 (타로/별자리 등) → **revise**
- **PO-002**: 허가되지 않은 격국/관계 코드 사용 → **revise**

#### 5️⃣ KO_FIRST_LABELS (KO-001~003) - Phase: both
- **KO-001**: label_ko 누락 → **revise**
- **KO-002**: KO-first 위반 (EN-only/EN-first) → **revise**
- **KO-003**: 톤 가이드 위반 (단정/예단) → **revise**

#### 6️⃣ HARM_GUARD (HG-001~003) - Phase: post
- **HG-001**: 의료적 단정/치료 주장 → **deny**
- **HG-002**: 법률/재무 보장 표현 → **deny**
- **HG-003**: 미성년/민감군 대상 조장 → **deny**

### 2.3 데이터 구조

#### GuardBundle (입력)
```python
@dataclass
class GuardBundle:
    module: str  # "llm_guard_v1.0"
    version: str  # "1.0.0"
    signature: str
    locale_used: str  # "ko-KR"
    inputs: GuardInputs
    checks: List[Check]  # 초기엔 빈 배열
    decision: Decision  # 초기엔 allow
    meta: GuardMeta

@dataclass
class GuardInputs:
    policy_refs: List[PolicyRef]
    evidence_refs: List[EvidenceRef]
    text_candidates: Optional[List[TextCandidate]]
    context: Optional[Dict]
```

#### GuardResult (출력)
```python
@dataclass
class GuardResult:
    checks: List[Check]
    decision: Decision
    meta: GuardMeta

@dataclass
class Check:
    id: str
    kind: Literal["schema", "policy", "evidence", "localization", "content", "trace", "determinism", "ci"]
    status: Literal["pass", "fail", "warn"]
    severity: Optional[Literal["minor", "major", "fatal"]]
    label_ko: str
    rule_id: str
    details: Dict

@dataclass
class Decision:
    verdict: Literal["allow", "deny", "revise"]
    reasons: List[Reason]
    suggested_fixes: List[str]
    patches: Optional[List[Patch]]

@dataclass
class Patch:
    action: Literal["insert", "replace", "remove", "append"]
    path: str  # JSON Pointer
    value: Any
```

### 2.4 핵심 알고리즘

#### 결정 사다리 (Decision Ladder)
```python
def aggregate(checks: List[Check]) -> Verdict:
    if any(c.severity == "fatal" for c in checks):
        return "deny"
    if any(c.severity == "major" for c in checks):
        return "revise"
    return "allow"
```

#### RFC8785 정규화 + SHA256
```python
def compute_hash(inputs: GuardInputs) -> str:
    canonical = rfc8785_canonicalize(inputs)
    return sha256(canonical).hexdigest()
```

---

## 3. Gap 분석

| 기능 | 현재 | 요구사항 | Gap |
|------|------|----------|-----|
| **Pre-Gen 검증** | ❌ 없음 | ✅ 필수 | 신규 구현 필요 |
| **Post-Gen 검증** | 부분적 (금지어만) | ✅ 6개 family | 확장 필요 |
| **Rule Families** | ❌ 없음 | ✅ 6개 (18개 규칙) | 신규 구현 필요 |
| **Decision Ladder** | ❌ 없음 | ✅ deny>revise>allow | 신규 구현 필요 |
| **Patch Generator** | ❌ 없음 | ✅ JSON Patch | 신규 구현 필요 |
| **RFC8785 정규화** | ❌ 없음 | ✅ 필수 | 신규 구현 필요 |
| **SHA256 해싱** | ❌ 없음 | ✅ 필수 | 신규 구현 필요 |
| **정책 서명 검증** | ❌ 없음 | ✅ 필수 | 신규 구현 필요 |
| **한국어 라벨** | ✅ 있음 (141개) | ✅ 필수 | 검증 로직 추가 |
| **텍스트 필터링** | 부분적 (금지어) | ✅ Rule-based | 확장 필요 |
| **스키마 검증** | 부분적 (Pydantic) | ✅ JSON Schema | 확장 필요 |

**커버리지**: 현재 **10%** → 목표 **100%**

---

## 4. 구현 계획

### Phase 1: Core Infrastructure (1-2일, 400-500줄)

**목표**: 데이터 구조 + 기본 플로우

#### 1.1 새 파일 생성
- `app/core/llm_guard_v1.py` (메인 클래스)
- `app/models/guard.py` (GuardBundle, GuardResult, Check, Decision, Patch)
- `app/core/guard_rules/` (규칙 디렉토리)
  - `__init__.py`
  - `base.py` (Rule 추상 클래스)
  - `determinism.py`
  - `trace_integrity.py`
  - `evidence_bound.py`
  - `policy_bound.py`
  - `ko_first_labels.py`
  - `harm_guard.py`

#### 1.2 기본 구조
```python
# app/core/llm_guard_v1.py
class LLMGuardV1:
    def __init__(self, policy: Dict):
        self.policy = policy
        self.pre_gen_rules = self._load_pre_gen_rules()
        self.post_gen_rules = self._load_post_gen_rules()

    def check(self, bundle: GuardBundle) -> GuardResult:
        checks = self.run_checks(bundle)
        verdict = self.aggregate(checks)
        fixes = self.suggest_fixes(checks) if verdict != "allow" else []
        patches = self.build_patches(bundle, fixes) if verdict == "revise" else []

        return GuardResult(
            checks=checks,
            decision=Decision(
                verdict=verdict,
                reasons=self.summarize(checks),
                suggested_fixes=fixes,
                patches=patches
            ),
            meta=self._build_meta(bundle)
        )

    def run_checks(self, bundle: GuardBundle) -> List[Check]:
        checks = []

        # Phase 구분
        phase = self._determine_phase(bundle)

        if phase == "pre" or phase == "both":
            for rule in self.pre_gen_rules:
                checks.append(rule.check(bundle))

        if phase == "post" or phase == "both":
            for rule in self.post_gen_rules:
                checks.append(rule.check(bundle))

        return checks

    def aggregate(self, checks: List[Check]) -> Verdict:
        if any(c.severity == "fatal" for c in checks if c.status == "fail"):
            return "deny"
        if any(c.severity == "major" for c in checks if c.status == "fail"):
            return "revise"
        return "allow"
```

### Phase 2: Rule Families (2-3일, 600-800줄)

**목표**: 18개 규칙 전부 구현

#### 2.1 Base Rule 클래스
```python
# app/core/guard_rules/base.py
from abc import ABC, abstractmethod

class Rule(ABC):
    def __init__(self, rule_id: str, label_ko: str, severity: str, policy: Dict):
        self.rule_id = rule_id
        self.label_ko = label_ko
        self.severity = severity
        self.policy = policy

    @abstractmethod
    def check(self, bundle: GuardBundle) -> Check:
        pass
```

#### 2.2 각 Family 구현
- **determinism.py**: DT-001, DT-002, DT-003
- **trace_integrity.py**: TR-001, TR-002
- **evidence_bound.py**: EV-001, EV-002, EV-003
- **policy_bound.py**: PO-001, PO-002
- **ko_first_labels.py**: KO-001, KO-002, KO-003
- **harm_guard.py**: HG-001, HG-002, HG-003

#### 2.3 예시: EV-002 (외부 사실 인용 금지)
```python
# app/core/guard_rules/evidence_bound.py
class EV002_ExternalFactsRule(Rule):
    def __init__(self, policy: Dict):
        super().__init__(
            rule_id="EV-002",
            label_ko="외부 사실 인용 금지(근거 누락)",
            severity="major",
            policy=policy
        )
        # 정책에서 패턴 로드
        rule_config = self._find_rule_config("EV-002")
        self.patterns = rule_config["post_gen_patterns"]["regex_any"]

    def check(self, bundle: GuardBundle) -> Check:
        if not bundle.inputs.text_candidates:
            return Check(
                id=self.rule_id,
                kind="content",
                status="pass",
                severity=None,
                label_ko=self.label_ko,
                rule_id=self.rule_id,
                details={}
            )

        for candidate in bundle.inputs.text_candidates:
            text = candidate.text
            for pattern in self.patterns:
                if re.search(pattern, text):
                    return Check(
                        id=self.rule_id,
                        kind="content",
                        status="fail",
                        severity=self.severity,
                        label_ko=self.label_ko,
                        rule_id=self.rule_id,
                        details={
                            "matched_pattern": pattern,
                            "text_snippet": text[:100]
                        }
                    )

        return Check(
            id=self.rule_id,
            kind="content",
            status="pass",
            severity=None,
            label_ko=self.label_ko,
            rule_id=self.rule_id,
            details={}
        )
```

### Phase 3: Decision Engine (1일, 200-300줄)

**목표**: Aggregation + Summarization

```python
def aggregate(self, checks: List[Check]) -> Verdict:
    """결정 사다리: deny > revise > allow"""
    failed = [c for c in checks if c.status == "fail"]

    if any(c.severity == "fatal" for c in failed):
        return "deny"
    if any(c.severity == "major" for c in failed):
        return "revise"
    return "allow"

def summarize(self, checks: List[Check]) -> List[Reason]:
    """실패한 체크만 요약 (top-k)"""
    failed = [c for c in checks if c.status == "fail"]
    sorted_failed = sorted(failed, key=lambda c: {"fatal": 0, "major": 1, "minor": 2}[c.severity])

    top_k = self.policy.get("aggregation", {}).get("explain_top_k", 5)

    return [
        Reason(
            rule_id=c.rule_id,
            label_ko=c.label_ko,
            severity=c.severity
        )
        for c in sorted_failed[:top_k]
    ]
```

### Phase 4: Patch Generator (1-2일, 300-400줄)

**목표**: revise 시 JSON Patch 생성

```python
def build_patches(self, bundle: GuardBundle, fixes: List[str]) -> List[Patch]:
    """수정 제안을 JSON Patch로 변환"""
    patches = []

    for fix in fixes:
        if "label_ko 누락" in fix:
            patches.extend(self._inject_missing_labels(bundle))
        elif "EN-only" in fix:
            patches.extend(self._normalize_ko_first(bundle))
        elif "단정 표현" in fix:
            patches.extend(self._replace_certainty(bundle))
        elif "면책 문구" in fix:
            patches.extend(self._insert_disclaimer(bundle))

    return patches

def _inject_missing_labels(self, bundle: GuardBundle) -> List[Patch]:
    """label_ko 누락 시 정책 사전 기반 자동 주입"""
    patches = []

    # trace에서 label_ko 누락 찾기
    for i, trace_item in enumerate(bundle.trace or []):
        if "label_ko" not in trace_item and "policy_rule_id" in trace_item:
            rule_id = trace_item["policy_rule_id"]
            label_ko = self._lookup_label_ko(rule_id)

            if label_ko:
                patches.append(Patch(
                    action="insert",
                    path=f"/trace/{i}/label_ko",
                    value=label_ko
                ))

    return patches
```

### Phase 5: RFC8785 + SHA256 (0.5일, 100-150줄)

**목표**: 결정성 보장

```python
# app/core/canonicalize.py
import json
import hashlib

def rfc8785_canonicalize(data: Dict) -> bytes:
    """
    RFC8785 JSON Canonicalization Scheme (JCS)
    - 키 정렬
    - 불필요한 공백 제거
    - 유니코드 정규화
    """
    canonical_str = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':')
    )
    return canonical_str.encode('utf-8')

def compute_hash(data: Dict) -> str:
    """RFC8785 정규화 후 SHA256 해시"""
    canonical = rfc8785_canonicalize(data)
    return hashlib.sha256(canonical).hexdigest()
```

### Phase 6: Integration (1일, 100-200줄)

**목표**: 기존 LLMGuard와 통합

#### 6.1 LLMGuard 업데이트
```python
# app/core/llm_guard.py
@dataclass(slots=True)
class LLMGuard:
    text_guard: TextGuard
    recommendation_guard: RecommendationGuard
    korean_enricher: KoreanLabelEnricher
    guard_v1: LLMGuardV1  # ← 추가

    @classmethod
    def default(cls) -> "LLMGuard":
        # LLM Guard v1.0 정책 로드
        guard_policy = load_llm_guard_policy()

        return cls(
            text_guard=TextGuard.from_file(),
            recommendation_guard=RecommendationGuard.from_file(),
            korean_enricher=KoreanLabelEnricher.from_files(),
            guard_v1=LLMGuardV1(policy=guard_policy)  # ← 추가
        )

    def prepare_payload(self, response: AnalysisResponse) -> dict:
        """Pre-Gen Hook 적용"""
        # 1. 기본 검증 + 한국어 라벨
        payload = response.model_dump()
        enriched = self.korean_enricher.enrich(payload)

        # 2. Pre-Gen 번들 생성
        bundle = self._create_pre_gen_bundle(enriched)

        # 3. Pre-Gen 검증
        result = self.guard_v1.check(bundle)

        # 4. deny 시 에러
        if result.decision.verdict == "deny":
            raise ValueError(f"Pre-Gen guard denied: {result.decision.reasons}")

        # 5. revise 시 패치 적용
        if result.decision.verdict == "revise" and result.decision.patches:
            enriched = self._apply_patches(enriched, result.decision.patches)

        return enriched

    def postprocess(
        self,
        original: AnalysisResponse,
        llm_payload: dict,
        *,
        structure_primary: str | None = None,
        topic_tags: Iterable[str] | None = None,
    ) -> AnalysisResponse:
        """Post-Gen Hook 적용"""
        # 1. 스키마 검증
        candidate = AnalysisResponse.model_validate(llm_payload)

        # 2. trace 불변성 (기존)
        if candidate.trace != original.trace:
            raise ValueError("LLM output modified trace metadata")

        # 3. Post-Gen 번들 생성
        bundle = self._create_post_gen_bundle(llm_payload, original)

        # 4. Post-Gen 검증
        result = self.guard_v1.check(bundle)

        # 5. deny 시 에러
        if result.decision.verdict == "deny":
            raise ValueError(f"Post-Gen guard denied: {result.decision.reasons}")

        # 6. revise 시 패치 적용
        if result.decision.verdict == "revise" and result.decision.patches:
            llm_payload = self._apply_patches(llm_payload, result.decision.patches)
            candidate = AnalysisResponse.model_validate(llm_payload)

        # 7. 기존 로직 (텍스트 가드, 추천 가드)
        notes = candidate.trace.get("notes")
        if isinstance(notes, str):
            candidate.trace["notes"] = self.text_guard.guard(notes, topic_tags or [])

        rec = self.recommendation_guard.decide(structure_primary=structure_primary)
        candidate.trace.setdefault("recommendation", rec)
        candidate.recommendation = candidate.recommendation.__class__(**rec)

        return candidate
```

### Phase 7: Testing (2-3일, 800-1000줄)

**목표**: 22개 구체적 케이스 + 10개 Property-based 테스트

#### 7.1 구체적 테스트 (test_llm_guard_v1_cases.py)
```python
import pytest
from app.core.llm_guard_v1 import LLMGuardV1
from app.models.guard import GuardBundle

class TestLLMGuardV1Cases:
    @pytest.fixture
    def guard(self):
        policy = load_llm_guard_policy()
        return LLMGuardV1(policy)

    def test_case_01_evidence_없이_자유_추정_deny(self, guard):
        """Case 01 — Evidence 없이 자유 추정 (deny)"""
        bundle = GuardBundle(
            module="llm_guard_v1.0",
            version="1.0.0",
            signature="PENDING",
            locale_used="ko-KR",
            inputs=GuardInputs(
                policy_refs=[...],
                evidence_refs=[]  # 비어있음!
            ),
            ...
        )

        result = guard.check(bundle)

        assert result.decision.verdict == "deny"
        assert any("EV-001" in r.rule_id for r in result.decision.reasons)

    def test_case_02_외부_사실_인용_revise(self, guard):
        """Case 02 — 외부 사실 인용(출처 없음) (revise)"""
        bundle = GuardBundle(
            ...
            inputs=GuardInputs(
                ...
                text_candidates=[
                    TextCandidate(
                        id="t1",
                        locale="ko-KR",
                        text="뉴스에서 보니 올해는 꼭 성공한다고 하네요."
                    )
                ]
            )
        )

        result = guard.check(bundle)

        assert result.decision.verdict == "revise"
        assert any("EV-002" in r.rule_id for r in result.decision.reasons)

    # ... 나머지 20개 케이스
```

#### 7.2 Property-based 테스트 (test_llm_guard_v1_properties.py)
```python
import pytest
from hypothesis import given, strategies as st

class TestLLMGuardV1Properties:
    def test_p1_determinism_hash_invariant(self, guard):
        """P1 — 결정성 해시 불변"""
        bundle = create_test_bundle()

        hashes = [guard.check(bundle).meta.hash_inputs for _ in range(100)]
        verdicts = [guard.check(bundle).decision.verdict for _ in range(100)]

        assert len(set(hashes)) == 1
        assert len(set(verdicts)) == 1

    def test_p3_ladder_determinism(self, guard):
        """P3 — 사다리 결정성 (deny > revise > allow)"""
        # fatal, major, minor 동시 발생
        bundle = create_bundle_with_all_severities()

        result = guard.check(bundle)

        assert result.decision.verdict == "deny"

    # ... 나머지 8개 property
```

---

## 5. 예상 작업량

| Phase | 기간 | 코드 줄 수 | 난이도 |
|-------|------|-----------|--------|
| Phase 1: Core Infrastructure | 1-2일 | 400-500줄 | 중 |
| Phase 2: Rule Families | 2-3일 | 600-800줄 | 높음 |
| Phase 3: Decision Engine | 1일 | 200-300줄 | 중 |
| Phase 4: Patch Generator | 1-2일 | 300-400줄 | 높음 |
| Phase 5: RFC8785 + SHA256 | 0.5일 | 100-150줄 | 낮음 |
| Phase 6: Integration | 1일 | 100-200줄 | 중 |
| Phase 7: Testing | 2-3일 | 800-1000줄 | 중 |
| **총계** | **8-12일** | **2,500-3,350줄** | **높음** |

---

## 6. 리스크 및 고려사항

### 6.1 기술적 리스크

1. **RFC8785 구현 복잡도**
   - Python 표준 라이브러리만으로 RFC8785 완전 구현 어려움
   - 외부 라이브러리 필요할 수 있음 (예: `canonicaljson`)

2. **정책 서명 검증**
   - 서명 알고리즘 미정 (RSA? Ed25519?)
   - 키 관리 전략 필요

3. **패치 적용 안정성**
   - JSON Patch 적용 시 구조 손상 위험
   - Rollback 메커니즘 필요

### 6.2 통합 리스크

1. **기존 코드 호환성**
   - 현재 LLMGuard 사용처 영향 분석 필요
   - 점진적 마이그레이션 전략

2. **성능 영향**
   - 18개 규칙 체크 시 지연 시간 증가
   - 캐싱/최적화 전략 필요

### 6.3 정책 유지보수

1. **정책 파일 관리**
   - `llm_guard_policy.json` 위치 확정
   - 버전 관리 및 마이그레이션 전략

2. **규칙 확장성**
   - 새 규칙 추가 시 인터페이스 안정성

---

## 7. 대안 및 권장사항

### 7.1 옵션 A: Full Implementation (권장)

**장점**:
- ✅ 정책 100% 준수
- ✅ 결정성 보장
- ✅ 프로덕션 레디

**단점**:
- ❌ 8-12일 소요
- ❌ 높은 복잡도

### 7.2 옵션 B: MVP (최소 기능)

**범위**:
- Phase 1-3만 구현 (Core + Rules + Decision)
- Patch Generator 제외
- RFC8785 간소화 (표준 JSON 정렬만)

**장점**:
- ✅ 4-5일 소요
- ✅ 핵심 검증 기능 확보

**단점**:
- ❌ revise 기능 부실 (패치 없음)
- ❌ 결정성 미보장

### 7.3 옵션 C: Incremental

**전략**:
1. Week 1: Core + DETERMINISM + HARM_GUARD (가장 중요)
2. Week 2: 나머지 Rule Families
3. Week 3: Patch Generator + Testing

**장점**:
- ✅ 점진적 가치 제공
- ✅ 리스크 분산

**단점**:
- ❌ 총 기간 더 길어질 수 있음

---

## 8. 다음 단계

### 즉시 결정 필요

1. **구현 범위 확정**
   - Full Implementation vs MVP vs Incremental?

2. **우선순위 확정**
   - 어떤 Rule Family가 가장 중요한가?
   - HARM_GUARD? DETERMINISM? KO_FIRST_LABELS?

3. **정책 파일 위치 확정**
   - `llm_guard_policy.json` 어디에 둘 것인가?
   - `saju_codex_batch_all_v2_6_signed/policies/`?

4. **서명 전략 확정**
   - 서명 알고리즘?
   - 키 관리?

### 구현 전 준비

1. **정책 파일 복사**
   ```bash
   cp llm_guard_policy.json saju_codex_batch_all_v2_6_signed/policies/
   cp llm_guard.schema.json saju_codex_batch_all_v2_6_signed/schemas/
   ```

2. **의존성 추가**
   ```toml
   # pyproject.toml
   dependencies = [
       ...
       "canonicaljson>=2.0",  # RFC8785
       "cryptography>=41.0",  # 서명 검증
   ]
   ```

3. **테스트 케이스 파일 준비**
   ```bash
   cp test_llm_guard_cases.md services/analysis-service/tests/
   cp test_llm_guard_properties.md services/analysis-service/tests/
   ```

---

## 9. 결론

LLM Guard v1.0은 **대규모 프로젝트**입니다. 현재 구현은 요구사항의 10%만 커버하며, 완전한 구현을 위해서는 **8-12일**의 개발 기간과 **2,500-3,350줄**의 코드가 필요합니다.

**권장 전략**: **Incremental 접근**
- Week 1: HARM_GUARD + DETERMINISM (가장 critical)
- Week 2: 나머지 Rule Families
- Week 3: Patch Generator + Full Testing

이렇게 하면 단계별로 가치를 제공하면서도, 리스크를 최소화할 수 있습니다.

---

**문서 버전**: 1.0.0
**분석자**: Ultrathink Analysis Engine
**최종 업데이트**: 2025-10-06
**상태**: 📋 계획 완료, 구현 결정 대기
