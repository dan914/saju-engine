# Gyeokguk Classifier v1.0 — Methodology (KO-first)

본 문서는 격국 분류 엔진 v1.0의 정책적 절차, 규칙표, 점수화 방식, 우선순위/타이브레이커, 예시 및 의사코드를 정리한다.

Stage‑1 하위 엔진(강약 v2.0.1, 지지십신 v1.1, Relation v1.0, Elemental Projection Policy)과 Evidence Builder 산출을 정책 기반으로 결합하여 정관격·칠살격·정재격·편재격·식신격·상관격·정인격·편인격 및 비견·겁재, **종격 4종(從兒·從財·從殺·從旺)**을 분류한다.

## 1) 입력 및 의존성

### inputs.context
- `day_master` (十干)
- `month_branch` (十二支)
- `season` (계절)
- `strength_state` (weak/balanced/strong)
- `climate` (temperature/humidity)

### evidence_refs
- **strength_v2** (>=2.0.1): 점수화(0~1), 상태 분류(weak/balanced/strong)
- **branch_tengods_v1.1** (>=1.1.0): 월령 득령, 십신벡터
- **relation_v1.0** (>=1.0.0): 三合·半合·六合·沖·刑·破·害·方/拱合 및 연쇄
- **elemental_projection_policy** (>=1.0.0): 강약·십신·관계·조후를 오행벡터로 투영
- (선택) **yongshin_v1.0**: 정합도(override 금지, 타이브레이커/신뢰도 반영)

---

## 2) 규칙표 (요지)

### 2.1 핵심 8格 (CORE)

**정관격(ZHENGGUAN)**: 正官 우세, 월령 득령, 일간 과강 금지. 보조: 관인상생, 재생관. 페널티: 관살혼잡, 상관견관.

**칠살격(QISHA)**: 七殺 우세, 살인상생 혹은 식상 제어 보조. 혼잡 패널티.

**정재격(ZHENGCAI)**: 正財 우세, 일간 너무 약하면 불가. 보조: 재생관. 패널티: 비겁탈재.

**편재격(PIANCAI)**: 偏財 우세, 유통성 강조. 보조: 식신생재. 패널티: 비겁탈재.

**식신격(SHISHEN)**: 食神 우세, 일정 강도 필요. 보조: 식신생재. 패널티: 식상극인.

**상관격(SHANGGUAN)**: 傷官 우세. 보조: 상관패인. 패널티/파격: 상관견관.

**정인격(YINSHOU)**: 正印 우세, 관인상생 유리. 패널티: 식상극인.

**편인격(PIANYIN)**: 偏印 우세, 살인상생 보조. 패널티: 식상극인.

### 2.2 동료격 (PEER)

**비견격(BIJIAN)**, **겁재격(JIECAI)**: 比劫 우세 + 강한 일간. 호신 보조, 탈재 패널티.

### 2.3 종격 (CONG) — 엄격 게이팅

**從兒(食傷從勢)**: 극약 일간(strength≤0.28) + 식상 일변도(≥0.50).

**從財**: 극약 일간 + 재성 일변도(≥0.55).

**從殺**: 극약 일간 + 관/살 일변도(≥0.55).

**從旺**: 극강 일간(strength≥0.72) + 비겁 일변도(≥0.55).

---

## 3) 점수화

### 3.1 원시점수

```
score_raw = Σ(core) + Σ(bonuses) + Σ(penalties)
```

- 규칙별 상한/하한 캡 적용(per_rule_max, per_pattern_bonus_max, per_pattern_penalty_min)
- 중복 가중 잔차(residual) 가드: 강약/십신/관계 동일 근거 중복 시 그룹 캡

### 3.2 정규화

**min_max[-30, +30] → [0, 100]**

상태부여:
- **成格**: score_norm≥60, core_coverage≥0.80, breakers 없음
- **假格**: score_norm≥40, core_coverage≥0.60, breakers 없음
- **破格**: 브레이커 1건 이상

---

## 4) 우선순위·타이브레이커

1. 가족 우선: **CONG > CORE > PEER > PSEUDO > MIX**
2. 점수 우위
3. 월령 적합도(month_command_fit)
4. 용신 정합도(yongshin_alignment) — 결과 교체 금지, 동점 해소용
5. 결정성 해시(사전순)

---

## 5) 신뢰도(confidence)

```
conf = clamp01(
  0.30*condition_coverage +
  0.25*strength_fit +
  0.25*month_command_fit +
  0.20*consistency
)
```

**Components**:
- **condition_coverage**: 핵심/보조/패널티 충족 비율(가중)
- **strength_fit**: 격별 요구 강약과의 적합 등급→[0..1]
- **month_command_fit**: 득령/계절성 평가→[0..1]
- **consistency**: top1 vs top2/3 점수 격차 비율

---

## 6) 트레이스(Trace) 구성

컴포넌트: `格局判定` / `成格條件` / `破格條件` / `扶抑` / `關係` / `조후` / `십신`

각 항목은 `policy_rule_id`와 KO 라벨 포함.

**예**:
- 格局判定: 정관격 기초 (GK-ZHENGGUAN-CORE, +12)
- 關係: 관인상생 (GK-ZHENGGUAN-BONUS-01, +6)
- 破格條件: 상관견관 (GK-ZHENGGUAN-PEN-02, −8)

---

## 7) 의사코드

```python
function classify_gyeokguk(inputs, evidences, policy):
  ctx = inputs.context
  e = evidences

  // 1) 선행 메트릭
  strength = e.strength_v2.score_normalized        // 0..1
  tenVec   = e.branch_tengods_v1_1.ten_god_vector  // map[十神]→0..1
  monthCmd = e.branch_tengods_v1_1.month_command   // 十神
  rels     = e.relation_v1_0.events                // set of relation codes
  proj     = e.elemental_projection.result_vector  // map[오행/십신군]→0..1
  ys_align = (e.yongshin_v1_0?.alignment_score) ?? 0.5

  candidates = []

  for pattern in policy.patterns:
    if pattern.family startsWith "CONG":
      if !gate_cong(pattern.gating, strength, proj, monthCmd): continue

    (raw, coverage, has_breaker, trace_items, month_fit) =
      score_pattern(pattern, strength, tenVec, monthCmd, rels, proj, ctx)

    score_norm = normalize(raw, policy.scoring.normalization)
    status = decide_status(score_norm, coverage, has_breaker, policy.scoring.status_thresholds)

    candidates.append({
      code: pattern.code,
      family: pattern.family,
      score_raw: raw,
      score_normalized: score_norm,
      status: status,
      month_command_fit: month_fit,
      yongshin_alignment: ys_align,
      trace: trace_items
    })

  // 2) 우선/타이브레이크
  sorted = sort_by_priority_and_tiebreakers(candidates, policy.priority, policy.tie_breakers)

  // 3) 신뢰도
  conf = confidence(sorted, coverage_of(sorted[0]), strength_fit(sorted[0]), sorted[0].month_command_fit, sorted)

  // 4) Evidence JSON
  return build_evidence(sorted, conf, inputs, policy)
```

---

## 8) 테스트 커버리지 가이드

**12+ 케이스**: 정관 성격/파격, 상관패인 성격, 칠살+살인상생, 從財/從殺 게이팅, 혼격/假格, 월령 전환, 강약 상치, 관계 충돌 등.

**속성**: 결정성 해시, 정규화 범위, 우선순위/타이브레이커 결정성, 從格 게이팅 불변식, 용신‑정합 단조성.

---

## 9) 제한 및 가드

- **LLM Guard v1.0** 적용: 정책 밖 추론 금지, Evidence 외 해석 금지.
- **Residual guard**: 십신↔강약 중복과가중 방지.
- **CI**: KO-first 라벨/스키마 적합/우선순위 일관성 검사/경계값 테스트.

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-05
**Author**: Saju Engine Development Team
**License**: Proprietary
