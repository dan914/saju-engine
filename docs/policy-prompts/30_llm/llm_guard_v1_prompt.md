# 🛡️ 실행 프롬프트 — LLM Guard v1 (Pre/Post) 스펙 v1.0

**ROLE**
너는 KO-first **안전·정합성 정책 엔지니어**다. **설명 금지**, **결정적 사양만** 출력한다.

**GOAL**
사주앱의 LLM 사용 구간에 대해 **Pre-Gen / Post-Gen** 2단계 **LLM Guard v1**의 **정책·스키마·패치 언어·테스트 명세**를 단일 문서로 산출한다.
출력물은 바로 코드화 가능한 **JSON Schema + 규칙표 + 케이스**로 구성한다.

---

## CONTEXT (고정 사실)
- LLM은 **설명/요약/코칭**만 수행한다.
- **정책 기반 산출물(간지/수치/버킷/격국/용신/운세 기둥)**은 엔진이 결정하며, LLM은 수정 금지.
- 입력 컨텍스트는 `/api/v1/report/saju` 응답(JSON) 중 **허용 경로(facts_paths)**에 한해 노출된다.
- 응답은 RFC-8785 **canonical JSON** 기준으로 `signatures.sha256` 서명 필드를 포함한다.

---

## OUTPUT ORDER (반드시 준수)
1) **가드 아키텍처 요약**(Pre-Gen / Post-Gen 단계 정의)
2) **정책 규칙표**(R1~R6) + 위반 예·처리 액션
3) **패치 언어(PL1)** 정의( op/start/end/text )
4) **JSON Schema 4종**: `GuardPolicy`, `PreGuard{Input,Output}`, `PostGuard{Input,Output}`
5) **이슈 코드 테이블**(CODE/심각도/설명/자동패치 가능 여부)
6) **예시 3건**(위반→패치 결과)
7) **단위/통합 테스트 명세**
8) **수용 기준(AC)**

---

## 1) 가드 아키텍처 요약

- **Pre-Gen**: 사용자 입력과 컨텍스트를 검사하여 **금지 의도/민감 범주**를 차단하고, **사실 경로 화이트리스트(facts_paths)**만 포함하는 **프롬프트 템플릿**을 생성한다.
  - 실패 시: `mode="safe_notice"`로 전환(카드만 제공, 텍스트 최소화).

- **Post-Gen**: 모델 산출 `llm_text`(및 선택적으로 `cards[]`)를 **정합성/안전성 검사** 후 **자동 패치**하거나 차단.
  - 우선순위: Grounding→Consistency→Scope→Privacy→Tone.
  - 결과: `decision ∈ {allow, patched, block}`.

---

## 2) 정책 규칙(R1~R6)

| ID | 규칙명 | 설명 | 위반 예 | 기본 액션 |
|---|---|---|---|---|
| **R1** | Grounding(사실연동) | 숫자·간지·날짜·퍼센트는 **허용 경로**의 값만 사용 | "10/12에 계약하세요" (컨텍스트에 없음) | `replace → generic_phrase` |
| **R2** | Consistency(정합성) | 용신/강약/버킷/간지 등은 **엔진 값과 일치**해야 함 | "신강"이라면서 버킷은 `weak` | `delete segment` |
| **R3** | Scope(민감주제) | 의료·법률·투자 **구체 행위** 금지(일반 습관 조언만) | "AETF 30% 매수" | `block_or_safe_notice` |
| **R4** | Tone(어조) | 단정·공포·숙명론 금지 → 코칭형으로 완화 | "반드시 실패합니다" | `replace → hedge_phrase` |
| **R5** | Privacy(개인정보) | 이름/성별/생년월일 외 PII 재노출 금지 | 전화/주소/이메일 언급 | `redact` |
| **R6** | Grounded Date Window | 월운 기간 외 **임의 날짜** 금지(예: `term_window` 밖) | 기간 밖 날짜 추천 | `replace → within_window_hint` |

**허용 경로 예(facts_paths subset)**
`analysis.wuxing.raw.percent.*`, `analysis.wuxing.status_tag.*`, `analysis.strength.*`,
`analysis.yongshin.*`, `analysis.luck.decades.*`, `analysis.luck.years.*`, `analysis.luck.months.*`,
`pillars.*`, `localization.ko`

**금지 패턴(예시, ko/en)**
- 의료: 치료/복용/처방/용량, "treat/cure/dose/prescribe"
- 법률: 고소/소송/계약 무효, "sue/illegal/void contract"
- 투자: 수익률 보장/매수·매도 지시, "buy/sell/guarantee return"
- 숙명론: "반드시/결정되어 있다/피할 수 없다"

---

## 3) 패치 언어(PL1)

```json
{
  "op": "replace | delete | redact",
  "start": 42,
  "end": 57,
  "text": "일반적인 정리·기록 습관을 우선하세요."  // op=replace 일 때만
}
```

- 인덱스는 UTF-16 code unit 기준.
- 여러 패치는 앞→뒤 순서로 적용.
- `redact`는 동일 길이 별표(*) 대체를 권장.

---

## 4) JSON Schema

### 4.1 GuardPolicy (정책 설정)
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "$id":"https://example.com/schemas/guard_policy_v1.schema.json",
  "type":"object",
  "required":["facts_paths","blocked_topics","tone","privacy","grounding","signatures"],
  "properties":{
    "facts_paths":{"type":"array","items":{"type":"string"}},
    "grounding":{
      "type":"object",
      "properties":{
        "allow_ganzhi": {"type":"boolean","default": true},
        "allow_percent": {"type":"boolean","default": true},
        "allow_dates_iso8601": {"type":"boolean","default": true},
        "date_window_sec": {"type":"integer","minimum":0,"default": 0}
      }
    },
    "blocked_topics":{
      "type":"object",
      "properties":{
        "medical":{"type":"array","items":{"type":"string"}},
        "legal":{"type":"array","items":{"type":"string"}},
        "finance":{"type":"array","items":{"type":"string"}}
      }
    },
    "tone":{
      "type":"object",
      "properties":{
        "banned_phrases":{"type":"array","items":{"type":"string"}},
        "hedge_phrases":{"type":"array","items":{"type":"string"}}
      }
    },
    "privacy":{
      "type":"object",
      "properties":{
        "allow_name":{"type":"boolean","default":true},
        "allow_gender":{"type":"boolean","default":true},
        "allow_birth":{"type":"boolean","default":true},
        "ban_patterns":{"type":"array","items":{"type":"string"}}
      }
    },
    "consistency":{
      "type":"object",
      "properties":{
        "enforce_yongshin":{"type":"boolean","default":true},
        "enforce_strength_bucket":{"type":"boolean","default":true}
      }
    },
    "signatures":{"type":"object","properties":{"sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"}}}
  },
  "additionalProperties": false
}
```

### 4.2 PreGuard

#### Input
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "$id":"https://example.com/schemas/preguard_input_v1.schema.json",
  "type":"object",
  "required":["message","intent","depth","context","policy"],
  "properties":{
    "message":{"type":"string","minLength":1,"maxLength":2000},
    "intent":{"type":"string","enum":["today","month","year","money","work","study","move","love","match","general"]},
    "depth":{"type":"string","enum":["auto","light","deep"]},
    "context":{"type":"object"},
    "policy":{"$ref":"https://example.com/schemas/guard_policy_v1.schema.json"}
  }
}
```

#### Output
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "$id":"https://example.com/schemas/preguard_output_v1.schema.json",
  "type":"object",
  "required":["mode","template","facts_paths","issues","signatures"],
  "properties":{
    "mode":{"type":"string","enum":["normal","safe_notice","blocked"]},
    "template":{"type":"string"},
    "facts_paths":{"type":"array","items":{"type":"string"}},
    "issues":{"type":"array","items":{"$ref":"https://example.com/schemas/guard_issue_v1.schema.json"}},
    "signatures":{"type":"object","properties":{"sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"}}}
  }
}
```

### 4.3 PostGuard

#### Input
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "$id":"https://example.com/schemas/postguard_input_v1.schema.json",
  "type":"object",
  "required":["llm_text","context","policy"],
  "properties":{
    "llm_text":{"type":"string","minLength":1},
    "cards":{"type":"array","items":{"type":"object"}},
    "context":{"type":"object"},
    "policy":{"$ref":"https://example.com/schemas/guard_policy_v1.schema.json"}
  }
}
```

#### Output
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "$id":"https://example.com/schemas/postguard_output_v1.schema.json",
  "type":"object",
  "required":["decision","issues","patches","text_final","signatures"],
  "properties":{
    "decision":{"type":"string","enum":["allow","patched","block"]},
    "issues":{"type":"array","items":{"$ref":"https://example.com/schemas/guard_issue_v1.schema.json"}},
    "patches":{"type":"array","items":{"$ref":"https://example.com/schemas/guard_patch_v1.schema.json"}},
    "text_final":{"type":"string"},
    "signatures":{"type":"object","properties":{"sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"}}}
  }
}
```

### 4.4 Issue/Patch Schemas

#### GuardIssue
```json
{
  "$id":"https://example.com/schemas/guard_issue_v1.schema.json",
  "type":"object",
  "required":["code","severity","message"],
  "properties":{
    "code":{"type":"string"},
    "severity":{"type":"string","enum":["low","medium","high","critical"]},
    "message":{"type":"string"},
    "path":{"type":["string","null"]},
    "span":{"type":["array","null"],"items":{"type":"integer"}}
  }
}
```

#### GuardPatch
```json
{
  "$id":"https://example.com/schemas/guard_patch_v1.schema.json",
  "type":"object",
  "required":["op","start","end"],
  "properties":{
    "op":{"type":"string","enum":["replace","delete","redact"]},
    "start":{"type":"integer","minimum":0},
    "end":{"type":"integer","minimum":0},
    "text":{"type":["string","null"]}
  }
}
```

---

## 5) 이슈 코드 테이블

| CODE | 심각도 | 설명 | 자동패치 |
|---|---|---|---|
| `GROUND_UNVERIFIED` | high | 컨텍스트에 없는 수치/날짜/간지 | ✔ replace/delete |
| `CONSIST_MISMATCH` | high | 엔진 값과 상충(용신/강약/간지 등) | ✔ delete |
| `SCOPE_RESTRICTED` | critical | 의료/법률/투자 구체 행위 | ▲ safe_notice / block |
| `TONE_FATALISM` | medium | 단정/숙명론 어휘 사용 | ✔ replace(hedge) |
| `PRIVACY_LEAK` | high | PII 노출(이름·성별·생년 제외) | ✔ redact |
| `DATE_OUT_OF_WINDOW` | high | term_window 밖 날짜 언급 | ✔ replace(within_window_hint) |
| `FORMAT_INVALID` | low | 잘못된 포맷(YYYY-MM 등) | ✔ replace |

---

## 6) 예시 (위반 → 패치)

### 6.1 Grounding 위반
**입력 llm_text**: "10/12 계약이 반드시 유리합니다."
**컨텍스트**: `analysis.luck.months["2025-10"].term_window = 10/08~11/07` (날짜 값 없음, 창만 있음)

**결과**:
```json
{
  "decision":"patched",
  "issues":[{"code":"GROUND_UNVERIFIED","severity":"high","message":"임의 날짜"}],
  "patches":[
    {"op":"replace","start":0,"end":14,"text":"기간 내 중요한 문서는 검토 후 진행이 유리합니다."},
    {"op":"replace","start":14,"end":22,"text":"지나치게 단정하지 말고"}
  ],
  "text_final":"기간 내 중요한 문서는 검토 후 진행이 유리합니다. 지나치게 단정하지 말고 상황에 맞춰 결정하세요.",
  "signatures":{"sha256":"<PLACEHOLDER>"}
}
```

### 6.2 Scope 위반(투자)
**입력**: "이번 달 AETF 30% 매수가 최선입니다."

**결과**:
```json
{
  "decision":"block",
  "issues":[{"code":"SCOPE_RESTRICTED","severity":"critical","message":"투자 구체 행위"}],
  "patches":[],
  "text_final":"안전: 투자·의료·법률의 구체 행위는 제공하지 않으며, 기록·예산·상담 등 일반적 습관을 권장합니다.",
  "signatures":{"sha256":"<PLACEHOLDER>"}
}
```

### 6.3 Consistency 위반(강약 상충)
**컨텍스트**: `analysis.strength.bucket="weak"`
**입력**: "당신은 신강이라 강하게 밀어붙이세요."

**결과**:
```json
{
  "decision":"patched",
  "issues":[{"code":"CONSIST_MISMATCH","severity":"high","message":"강약 상충"}],
  "patches":[{"op":"replace","start":4,"end":13,"text":"약한 편이므로 기본 루틴을 지키며"}],
  "text_final":"당신은 약한 편이므로 기본 루틴을 지키며 점진적으로 진행하세요.",
  "signatures":{"sha256":"<PLACEHOLDER>"}
}
```

---

## 7) 테스트 명세

### 단위(Pre-Gen)
- 의료/법률/투자 키워드 탐지 → `mode="safe_notice"`
- `facts_paths` 화이트리스트 외 경로 제거 확인

### 단위(Post-Gen)
- **Grounding**: 임의 수치/간지/날짜 탐지·치환
- **Consistency**: 용신·강약·간지 상충 탐지·삭제
- **Privacy**: 이메일/전화/주소 마스킹
- **Tone**: 금지 어휘 → hedge 치환
- **Date Window**: `term_window` 밖 날짜 → 범용 문구 치환

### 통합
- `/chat/send(deep)` 성공 플로우에서 `reserve→finalize`와 Guard 패치 결과의 서명 필드 생성 확인
- LLM 산출이 차단될 경우 카드만 응답 경로로 전환

---

## 8) 수용 기준(AC)
- Pre/Post 두 단계 모두 스키마·규칙·패치 언어·이슈코드가 완비되어야 함
- 예시 3건이 정책→패치→최종 텍스트 흐름을 보여야 함
- JSON Schema는 draft-2020-12 지정 및 필수 키 포함
- Post-Gen 결과는 항상 `signatures.sha256` 필드를 포함

---

## NOW OUTPUT
위 형식을 그대로 따라 LLM Guard v1 사양 문서를 생성하라. 불필요한 설명·주석 없이 정책·스키마·표·예시·테스트만 출력.
