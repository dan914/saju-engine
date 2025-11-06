# Yongshin Selector v1.0 — I/O 예시

## 입력

```json
{
  "day_master_gan": "乙",
  "day_master_element": "목",
  "strength": { "score": 0.38, "type": "신약" },
  "elements_distribution": { "목":0.16, "화":0.18, "토":0.22, "금":0.22, "수":0.22 },
  "relation_summary": { "sanhe":0.90, "sanhe_element":"수", "chong":0.20, "ganhe":0.10, "relation_hits":2, "relation_misses":0 },
  "climate": { "season_element":"수", "support":"강함" },
  "shensha": ["천을귀인"],
  "context": { "month_branch":"子", "strict": true }
}
```

## 출력 (예시)

```json
{
  "policy_version": "yongshin_v1.0.0",
  "yongshin": ["목","화"],
  "bojosin": ["목"],
  "gisin": ["금"],
  "confidence": 0.84,
  "scores": { "목":0.61, "화":0.54, "토":0.47, "수":0.46, "금":0.31 },
  "rules_fired": ["BIN:weak","REL:sanhe>0.7","CLIMATE:support+","DIST:deficit[목]"],
  "rationale": ["신약 → 인성·비겁 선호","수국 삼합이 목 생조에 우호","계절 수생목 유리","금 과다 억제 필요"],
  "explain": "신약형으로 생조 우선. 수국 삼합과 계절이 목/화를 밀어줌."
}
```

## 핵심 로직

1. **강약 구간 판정** (`strength.score` → weak/balanced/strong)
2. **기본 선호도** (weak: 인성·비겁, strong: 식상·관·재)
3. **관계 바이어스** (삼합/충/간합 등 가중치 적용)
4. **계절 바이어스** (season_element 상생/상극)
5. **분포 편차 보정** (과부족 오행 조정)
6. **최종 정렬** (상위→용신, 중간→보조신, 하위→기신)

## 신뢰도 (Confidence)

- **Base**: 0.70~0.80 (강약 구간별)
- **Relation**: +0.04 per hit, -0.03 per miss
- **Climate**: +0.03
- **Range**: 0.40~0.98

## 활용

LLM Guard v1.0의 `EVIDENCE_BOUND` 규칙에서 `yongshin` 배열을 참조하여:
- 용신 관련 조언만 허용
- 기신 강화 조언 차단
- 보조신 언급은 맥락 내 허용
