# Evidence Spec — branch_tengods (KO-first)

## 공통 헤더

```json
{
  "module": "branch_tengods",
  "policy_version": "1.1",
  "policy_signature": "<SHA256 by CI>",
  "locale_used": "ko-KR",
  "dependencies": { "sixty_jiazi", "elements_distribution", "localization_ko", "localization_en" }
}
```

## 입력 필드

```json
{
  "day_stem": { "stem": "甲", "element": "木", "polarity": "陽" },
  "branch": "巳",
  "hidden_list": [
    {"stem":"丙","element":"火","polarity":"陽","role":"primary"},
    {"stem":"庚","element":"金","polarity":"陽","role":"secondary"},
    {"stem":"戊","element":"土","polarity":"陽","role":"tertiary"}
  ]
}
```

## 단계(trace) 배열 원형

각 hidden에 대해 아래 형태로 기록:

```json
{
  "stem": "丙",
  "element": "火",
  "polarity": "陽",
  "role": "primary",
  "role_weight": 1.0,
  "relation_base": "wo_sheng",
  "parity": "same",
  "ten_god_code": "SIK",
  "ten_god_label_ko": "식신",
  "local_weight": 1.0
}
```

## 집계(aggregation)

```json
{
  "ten_god_weights_before_norm": {
    "SIK": 1.0,
    "PG": 0.6,
    "PJ": 0.3
  },
  "normalized": {
    "SIK": 0.5263,
    "PG": 0.3158,
    "PJ": 0.1579
  },
  "top_k_applied": 3,
  "threshold": 0.05
}
```

## 출력

```json
{
  "top_tengods": [
    {"code":"SIK","label_ko":"식신","label_zh":"食神","label_en":"Food God","weight":0.5263},
    {"code":"PG","label_ko":"편관","label_zh":"七殺","label_en":"Seven Killings","weight":0.3158},
    {"code":"PJ","label_ko":"편재","label_zh":"偏財","label_en":"Indirect Wealth","weight":0.1579}
  ],
  "others": []
}
```

## JSON 예시 A — 甲日 × 巳지

```json
{
  "module": "branch_tengods",
  "policy_version": "1.1",
  "policy_signature": "<SHA256>",
  "locale_used": "ko-KR",
  "inputs": {
    "day_stem": {"stem":"甲","element":"木","polarity":"陽"},
    "branch": "巳"
  },
  "trace": [
    {"stem":"丙","element":"火","polarity":"陽","role":"primary","role_weight":1.0,"relation_base":"wo_sheng","parity":"same","ten_god_code":"SIK","ten_god_label_ko":"식신","local_weight":1.0},
    {"stem":"庚","element":"金","polarity":"陽","role":"secondary","role_weight":0.6,"relation_base":"ke_wo","parity":"same","ten_god_code":"PG","ten_god_label_ko":"편관","local_weight":0.6},
    {"stem":"戊","element":"土","polarity":"陽","role":"tertiary","role_weight":0.3,"relation_base":"wo_ke","parity":"same","ten_god_code":"PJ","ten_god_label_ko":"편재","local_weight":0.3}
  ],
  "aggregation": {
    "ten_god_weights_before_norm": {"SIK":1.0,"PG":0.6,"PJ":0.3},
    "normalized": {"SIK":0.5263,"PG":0.3158,"PJ":0.1579},
    "top_k_applied": 3,
    "threshold": 0.05
  },
  "output": {
    "top_tengods": [
      {"code":"SIK","label_ko":"식신","label_zh":"食神","label_en":"Food God","weight":0.5263},
      {"code":"PG","label_ko":"편관","label_zh":"七殺","label_en":"Seven Killings","weight":0.3158},
      {"code":"PJ","label_ko":"편재","label_zh":"偏財","label_en":"Indirect Wealth","weight":0.1579}
    ]
  }
}
```

## JSON 예시 B — 丙日 × 丑지

```json
{
  "module": "branch_tengods",
  "policy_version": "1.1",
  "policy_signature": "<SHA256>",
  "locale_used": "ko-KR",
  "inputs": {
    "day_stem": {"stem":"丙","element":"火","polarity":"陽"},
    "branch": "丑"
  },
  "trace": [
    {"stem":"己","element":"土","polarity":"陰","role":"primary","role_weight":1.0,"relation_base":"wo_sheng","parity":"diff","ten_god_code":"SANG","ten_god_label_ko":"상관","local_weight":1.0},
    {"stem":"癸","element":"水","polarity":"陰","role":"secondary","role_weight":0.6,"relation_base":"ke_wo","parity":"diff","ten_god_code":"JG","ten_god_label_ko":"정관","local_weight":0.6},
    {"stem":"辛","element":"金","polarity":"陰","role":"tertiary","role_weight":0.3,"relation_base":"wo_ke","parity":"diff","ten_god_code":"JJ","ten_god_label_ko":"정재","local_weight":0.3}
  ],
  "aggregation": {
    "ten_god_weights_before_norm": {"SANG":1.0,"JG":0.6,"JJ":0.3},
    "normalized": {"SANG":0.5263,"JG":0.3158,"JJ":0.1579},
    "top_k_applied": 3,
    "threshold": 0.05
  },
  "output": {
    "top_tengods": [
      {"code":"SANG","label_ko":"상관","label_zh":"傷官","label_en":"Hurting Officer","weight":0.5263},
      {"code":"JG","label_ko":"정관","label_zh":"正官","label_en":"Direct Officer","weight":0.3158},
      {"code":"JJ","label_ko":"정재","label_zh":"正財","label_en":"Direct Wealth","weight":0.1579}
    ]
  }
}
```
