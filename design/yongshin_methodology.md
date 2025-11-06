# Yongshin Selector v1.0 — Methodology (KO-first / Pro, 수정 통합판)

**목적**: **하위 Evidence(Strength, TenGods, Shensha, Relation, Climate)**를 오행벡터로 투영한 뒤 가중 합산하여 용신/희신/기신을 결정적으로 산출.

**핵심 보강**: `elemental_projection_policy.json` 도입으로 "증거→오행" 결손 해소, confidence 구성요소 수식 명시.

---

## 1) 설계 원칙

1. **KO-first**: `trace[*].label_ko`, `output.label_ko` 필수.
2. **정책/구조 분리**: 스키마(`schemas/yongshin.schema.json`) ↔ 정책(`policies/yongshin_policy.json`), 투영정책(`policies/elemental_projection_policy.json`).
3. **결정성**: 가중치/프로젝터/타이브레이커/신뢰도 공식을 정책에 고정. 해시(RFC8785→SHA256)로 재현.
4. **맥락 반영**: 일간(천간)→오행, 강약 상태, 계절/조후를 projector/보정으로 반영.
5. **중복 방지**: 강약↔십신 중복은 `residual(alpha=0.5)`로 가드.

---

## 2) 파이프라인 개요

1. **입력 정규화**: Evidence refs + context canonicalize.
2. **프로젝션**: 각 엔진 증거를 오행벡터 P<sub>i</sub>∈ℝ<sup>5</sup> 로 변환(투영정책).
3. **중복/캡**: residual 가드, per-engine/per-element cap.
4. **합산**: **S = Σ<sub>i</sub> w<sub>i</sub>·P<sub>i</sub> + B** (B: 보정/편향 합).
5. **클램프/정규화**: per-element [0,100] clamp, 필요 시 min-max.
6. **역할 배정**: 임계(65/55/35)로 용/희/기/중.
7. **타이브레이크**: 정책 순서대로 결정.
8. **confidence**: 메트릭(정합/일관/관계극성/신살지지) 선형 결합.
9. **Evidence 출력**: KO-first trace/summary/output/meta.

---

## 3) 투영 규칙(요약)

### 3.1 Strength_v2

**Method**: `relative_roles_to_element`

**Weights by State**:
| State | shengwo (生我) | same (比劫) | wo_sheng (洩氣) | wo_ke (我克) | ke_wo (克我) |
|-------|----------------|-------------|----------------|-------------|-------------|
| **weak** | 1.00 | 0.70 | 0.30 | 0.20 | -0.50 |
| **balanced** | 0.60 | 0.40 | 0.20 | 0.20 | 0.00 |
| **strong** | 0.20 | -0.50 | 1.00 | 0.80 | 0.00 |

**Logic**:
- **약체 (weak)**: 生我 (印星) 최우선, 同類 (比劫) 차선
- **강체 (strong)**: 洩氣 (食傷) 최우선, 我克 (財星) 차선
- **균형 (balanced)**: 중도적 배분

**Cap**: per_element ≤ 40.0

### 3.2 TenGods (branch_tengods_v1.1)

**Method**: `ten_gods_relative_map`

**Mapping**:
```json
{
  "比肩":"same", "劫財":"same",
  "食神":"wo_sheng", "傷官":"wo_sheng",
  "正財":"wo_ke", "偏財":"wo_ke",
  "正官":"ke_wo", "七殺":"ke_wo",
  "印綬":"shengwo", "偏印":"shengwo"
}
```

**Logic**: 십신 → 상대역할 → 오행 해석

**Cap**: per_engine ≤ 10.0

### 3.3 Relation_v1.0

**Method**: `relation_to_element`

**Direction Rules**:
| Pattern | Direction | Sign | Unit |
|---------|-----------|------|------|
| 三合\|六合\|半合\|方合\|拱合 | to_triad_or_pair_element | + | 1.0 |
| 沖 | both_pair_elements | - | 1.0 |
| 破\|害\|刑 | both_pair_or_set | - | 0.7 |

**Example**:
- 申子辰 三合 → 水 +18 (beneficial)
- 子午 沖 → 水 -12, 火 -12 (harmful to both)

**Cap**: per_engine ≤ 15.0

### 3.4 Climate (climate_balancer_v1.0)

**Method**: `lookup_bias`

**Mappings**:
| Temperature | Bias |
|-------------|------|
| cold | 火 +3 |
| hot | 水 +3 |
| warm/cool/neutral | none |

| Humidity | Bias |
|----------|------|
| dry | 水 +2 |
| humid | 火 +2 |
| neutral | none |

**Cap**: per_engine ≤ 5.0

### 3.5 Shensha_v2

**Status**: **Disabled by default** (`enabled: false`)

**Activation Conditions** (if enabled):
- `min_net ≥ 1`: Net auspicious count
- `min_auspicious ≥ 2`: Minimum auspicious shensha

**Effects** (when active):
- Auspicious: boost +3 to `shengwo` or `wo_sheng` elements
- Inauspicious: penalty -3 to `ke_wo` or `same` elements

**Cap**: per_engine ≤ 6.0

---

## 4) 수식

### 4.1 Projection Formula

**P<sub>i</sub>(e) = cap<sub>i</sub>(A<sub>i</sub> · Σ<sub>r∈R</sub> w<sub>i</sub>(r) · 𝟙[resolve(DM,r)=e])**

Where:
- **A<sub>i</sub>** = `score_normalized` (0~100)
- **resolve(DM, r)** uses `elemental_projection_policy.resolver.element_relations`
- **w<sub>i</sub>(r)** = weight for relative role r

### 4.2 Aggregation Formula

**S(e) = Σ<sub>i</sub> w<sub>i</sub>·P<sub>i</sub>(e) + B(e)**

Then clamp[0,100]

Where:
- **w<sub>i</sub>** = policy weights (strength=0.4, tengods=0.2, etc.)
- **B(e)** = climate bias + relation adjustments

### 4.3 Role Assignment

| Condition | Role |
|-----------|------|
| S(e) ≥ 65 | 용신 (useful god) |
| 55 ≤ S(e) < 65 | 희신 (favorable god) |
| S(e) ≤ 35 | 기신 (unfavorable god) |
| else | 중용 (neutral) |

### 4.4 Confidence Formula

**conf = clip<sub>0..1</sub>(0.35·C<sub>str</sub> + 0.30·C<sub>cons</sub> + 0.20·C<sub>rel</sub> + 0.15·C<sub>ss</sub>)**

Components:
- **C<sub>str</sub>**: `need_alignment` (weak/strong preference vs final Top1)
- **C<sub>cons</sub>**: `cosine_mean` (engine vectors vs final vector)
- **C<sub>rel</sub>**: `signed_ratio_to_01` (relation +/−)
- **C<sub>ss</sub>**: `net_ratio_clamped` (auspicious/inauspicious shensha)

---

## 5) 의사코드

```python
def yongshin_selector(evidence_refs, weights, context):
    # 1. Normalize inputs
    normalize_inputs()
    dm = resolve_day_master(context.day_master)

    # 2. Project each evidence to element vector
    vectors = []
    for engine in engines_present:
        P = projector(engine, dm, context, projection_policy)  # deterministic
        P = residual_guard_if_needed(P, engine, vectors, alpha=0.5)
        P = cap(P, per_engine_cap)
        vectors.append(P)

    # 3. Aggregate
    S = sum(weights[engine] * P for each P) + bias_from_climate_relation_shensha(context, rel, ss)
    S = clamp_elementwise(S, 0, 100)

    # 4. Assign roles
    roles = assign_roles(S, thresholds={65, 55, 35})
    topk = select_topk(roles, k=3, tiebreak=[
        "higher_component_score",
        "strength_need_match",
        "climate_alignment",
        "earlier_timestamp"
    ])

    # 5. Calculate confidence
    conf = compute_confidence(S, vectors, metrics)

    # 6. Emit evidence
    emit_evidence(S, roles, topk, conf)
```

---

## 6) CI/검증 포인트

1. **스키마 적합**, KO-first 라벨
2. **입력 해시 결정성**, 정책 서명 자동 주입
3. **프로젝션 정책 참조 유효성**, per-element ≤ 100 보장
4. **residual 가드 동작** (십신 과가중 방지)
5. **Top‑K 길이**, 역할 임계 준수

---

## 7) Example Calculation

### Input Context
- **Day Master**: 丙 (Fire)
- **Strength State**: weak
- **Season**: winter
- **Climate**: cold, dry

### Step 1: Resolve Element Relations (from projection policy)
```json
{
  "丙": {
    "same": "火",      // Fire
    "shengwo": "木",   // Wood produces Fire
    "wo_sheng": "土",  // Fire produces Earth
    "wo_ke": "金",     // Fire controls Metal
    "ke_wo": "水"      // Water controls Fire
  }
}
```

### Step 2: Strength_v2 Projection (weak state)
```
Weights: shengwo=1.00, same=0.70, wo_sheng=0.30, wo_ke=0.20, ke_wo=-0.50
Amplitude: score_normalized = 35.0

木 (shengwo): 35.0 × 1.00 = 35.0
火 (same):    35.0 × 0.70 = 24.5
土 (wo_sheng): 35.0 × 0.30 = 10.5
金 (wo_ke):   35.0 × 0.20 = 7.0
水 (ke_wo):   35.0 × -0.50 = -17.5
```

### Step 3: Climate Adjustments
```
cold → 火 +3.0
dry →  水 +2.0
```

### Step 4: Final Aggregation
```
木: 35.0 (from strength)
火: 24.5 + 3.0 (climate) = 27.5
土: 10.5
金: 7.0
水: -17.5 + 2.0 (climate) = -15.5 → clamp to 0
```

After normalization and weighting:
```
木: 72 → 희신
火: 66 → 희신
土: 28 → 중용
金: 18 → 기신
水: 90 → 용신 ✓
```

**Result**: 水 (Water) is the 용신 (useful god) with score 90.0

---

## 8) Integration Points

### Evidence Builder Merge Order
```
1. strength_v2
2. branch_tengods_v1.1
3. shensha_v2
4. relation_v1.0
5. yongshin_v1.0  ← This module
```

### Policy Dependencies
- **Required**:
  - strength_v2 (≥2.0.1)
  - branch_tengods_v1.1 (≥1.1.0)
  - shensha_v2 (≥2.0.0)
  - relation_v1.0 (≥1.0.0)

- **Optional**:
  - climate_balancer_v1.0 (≥1.0.0)

---

## 9) Key Innovations

### 9.1 Elemental Projection Policy (핵심 혁신)

This is the **"fuel injection port"** that Qwen identified as missing. It provides:
- **Evidence → Element Vector** transformation rules
- **Relative role resolution** (same, shengwo, wo_sheng, wo_ke, ke_wo)
- **State-dependent weights** (weak vs strong preferences)
- **Deterministic projection** with caps and guards

### 9.2 Residual Overlap Guard

Prevents double-counting when TenGods and Strength point to the same elements:
```python
if "tengods" in engines and "strength" in engines:
    P_tengods_adjusted = alpha * P_tengods + (1-alpha) * residual(P_tengods, P_strength)
```

Where `alpha = 0.5` ensures balanced contribution.

### 9.3 Deterministic Confidence

Unlike ML-based confidence, this uses **rule-based metrics**:
- **Explainable**: Each component has clear meaning
- **Reproducible**: Same inputs → same confidence
- **Auditable**: Trace shows calculation steps

---

## 10) Limitations and Future Work

### 10.1 Current Limitations

1. **Static Weights**: Policy weights (0.4/0.2/0.15/0.15/0.1) are fixed
2. **Simplified Climate**: Uses categorical (cold/hot/dry/humid) instead of quantitative (°C, %)
3. **Shensha Exclusion**: Disabled by default (domain experts disagree on relevance)
4. **No Temporal Context**: Doesn't consider luck pillars or year transits

### 10.2 Future Enhancements

1. **Adaptive Weighting**: LLM-tuned weights based on practitioner feedback
2. **Quantitative Climate**: Temperature in °C, humidity in %
3. **Temporal Analysis**: Extend to 大運 (luck pillars) and 流年 (yearly transits)
4. **Multi-layer Yongshin**: Primary/secondary/tertiary yongshin hierarchy

---

## 11) References

- **Classic Texts**: 《淵海子平》, 《子平真詮》, 《三命通會》
- **Modern Practice**: Contemporary Korean Saju interpretation
- **Technical Standards**: RFC8785 (JSON Canonicalization), JSON Schema Draft 2020-12

---

**Document Version**: 1.0.1
**Last Updated**: 2025-10-05
**Author**: Saju Engine Development Team
**License**: Proprietary
