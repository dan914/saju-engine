# 🧩 실행 프롬프트 — LLM 템플릿 5종(오행/용신/강약/대운/연·월운) v1.0

**ROLE**
너는 **KO-first 템플릿 엔지니어**다. **설명 금지**, **결정적 산출물만** 출력한다.

**GOAL**
아래 5개 주제의 **문장 템플릿 팩**을 **단일 JSON**으로 산출하라.
각 주제마다 **Light(≤300t)** / **Deep(≤900t)** / **PDF(≤1300t)** 3등급 버전과, 필수 **facts_keys**(필드 경로) 목록을 포함한다.
템플릿은 **사실 슬롯**만 사용하고, 숫자/간지/연·월 등 **추가 생성 금지**(컨텍스트 값만 참조).

**TEMPLATES (5)**
1) `wuxing_summary` — 오행 분포 요약 및 균형 코칭
2) `yongshin_explain` — 용신 유형/오행/근거 설명
3) `strength_explain` — 신강/신약 점수·버킷 해석
4) `decades_commentary` — 대운(10년 단위) 흐름 요약 코멘트
5) `annual_monthly_commentary` — 연운·월운 핵심 포인트 + 7일/1기 티저

---

## CONTEXT MAP (팩트 경로; /report/saju 응답 기준)
- 일반: `pillars.*`, `analysis.*`, `localization.ko`
- 오행: `analysis.wuxing.raw.percent.{木,火,土,金,水}`, `analysis.wuxing.status_tag`, `analysis.day_master.element`(= `pillars.day.stem` 파생 KO)
- 용신: `analysis.yongshin.{type,elements[],rationale.evidence[]}`, `analysis.strength.bucket`
- 강약: `analysis.strength.{score,bucket,factors[]}`
- 대운: `analysis.luck.decades.{start_age,direction,pillars[].{age,pillar,ten_god,stage}}`
- 연운: `analysis.luck.years.{YYYY}.{pillar,ten_god,stage?}`
- 월운: `analysis.luck.months.{YYYY-MM}.{pillar,ten_god,stage?,term_window.{start,end}}`

> **금지**: 템플릿 본문에서 위 경로 외 값(추가 숫자·날짜·간지)을 **창작 금지**.

---

## SAFETY & GUARD (반드시 준수)
- **Grounding**: 숫자·간지·연·월은 **facts_keys**에 한함. 없으면 출력하지 말고 `{{MISSING(...)}}` 사용.
- **Scope**: 의료/법률/투자 **구체 조언 금지**. 일상/습관/커뮤니케이션 중심 코칭.
- **Tone**: 단정/공포/숙명론 금지. **코칭형**(선택지/대안 제시).
- **Privacy**: 사용자 신상 재노출 금지(이름/생년 제외).
- **Consistency**: 용신/강약/버킷/날짜가 컨텍스트와 상충 시, 문장 **생략**.
- **Fallback**: 필수 슬롯 누락 시 **안전 답변**: "확인된 정보 범위에서만 안내합니다." 한 줄 + 가능한 문단만 출력.

---

## OUTPUT FORMAT (단일 JSON; draft-like)
- **반드시 아래 스키마로만 출력**: 불필요한 설명/주석 금지.

```json
{
  "pack_id": "llm_templates_5pack_v1",
  "lang": "ko-KR",
  "templates": {
    "<topic>": {
      "facts_keys": ["<dot.path>", "..."],
      "light": "<TEMPLATE_TEXT>",
      "deep": "<TEMPLATE_TEXT>",
      "pdf": "<TEMPLATE_TEXT>"
    }
  }
}
```

### Placeholder 규칙
- **변수**: `{{analysis.wuxing.raw.percent.木}}`, `{{analysis.yongshin.elements[0]}}`
- **조건(최소한)**: `{{? analysis.wuxing.status_tag.金 == 'over' }} ... {{/}}`
- **선택 출력**: `{{opt analysis.yongshin.elements}}수(⽔){{/opt}}` (배열 있으면 첫 요소만 명시)
- **누락 경고**: `{{MISSING('analysis.luck.months')}}` (Guard가 후처리로 제거/대체)
- **템플릿 엔진 가정**: `{{...}}` 값 치환, `{{? cond}}...{{/}}` 조건, `{{opt key}}...{{/opt}}` 존재 시만 출력. 반복문/정렬 없음.

---

## STYLE GUIDE
- 문단 1~3개. 제목 한 줄(선택) + 핵심 요약 1문장 + 근거 2~3개 + 실행 팁 1~2개.
- 고유명/한자 표기는 한글 우선, 필요 시 병기: 예) "금(金)".
- 날짜/기간 언급은 컨텍스트 값만(예: `{{term_window.start}}`), 상대표현(이번/다음)은 금지.
- 긍정/중립 어투: "권장/피하기보단/정리·기록/체크리스트".
- 불가: 점괘식 확정, 재무 추정, 의학적 처방, 법률 판단.

---

## TEMPLATE SPEC (5 Topics)

### 1) wuxing_summary
**facts_keys (예시)**
- `analysis.wuxing.raw.percent.{木,火,土,金,水}`
- `analysis.wuxing.status_tag`
- `analysis.day_master.element`

**light**
```
요약: 현재 오행 분포에서 {{analysis.wuxing.status_tag.top?}}값이 두드러집니다.
{{? analysis.wuxing.status_tag.金 == 'over'}}금(金)이 강조되어 규칙·정리·문서 기반 정돈이 유리합니다.{{/}}
{{? analysis.wuxing.status_tag.木 == 'under'}}목(木)이 약하므로 계획 대비 실행 체크리스트를 간단히 운용하세요.{{/}}
실천 팁: 오늘 할 일 3가지를 **기록→정리→확인** 순으로 마무리해 보세요.
```

**deep**
```
오행 분포 정리:
- 목(木) {{analysis.wuxing.raw.percent.木}}%, 화(火) {{analysis.wuxing.raw.percent.火}}%, 토(土) {{analysis.wuxing.raw.percent.土}}%, 금(金) {{analysis.wuxing.raw.percent.金}}%, 수(⽔) {{analysis.wuxing.raw.percent.水}}%.
핵심: {{analysis.day_master.element}} 기준으로 {{analysis.wuxing.status_tag.focus}}가 흐름을 좌우합니다.
근거:
1) {{? analysis.wuxing.status_tag.金 == 'over'}}정리/규칙/마감 준수에 강점.{{/}}
2) {{? analysis.wuxing.status_tag.木 == 'under'}}새 계획 남발보다 기존 계획의 실행률 관리가 우선.{{/}}
실천: 주 2회 **정리 타임**을 캘린더에 고정하고, 완료 체크를 남겨두세요.
```

**pdf**
```
[오행 분포 리포트]
분포: 목 {{analysis.wuxing.raw.percent.木}}% · 화 {{analysis.wuxing.raw.percent.火}}% · 토 {{analysis.wuxing.raw.percent.土}}% · 금 {{analysis.wuxing.raw.percent.金}}% · 수 {{analysis.wuxing.raw.percent.水}}%
요약: {{analysis.day_master.element}} 기준, {{analysis.wuxing.status_tag.summary}}.
해석 포인트:
- 과다: {{? analysis.wuxing.status_tag.金 == 'over'}}금(金) 중심 — 규칙, 검토, 문서화 강화.{{/}}
- 부족: {{? analysis.wuxing.status_tag.木 == 'under'}}목(木) 보완 — 실행 체크리스트·정기 점검.{{/}}
권장 루틴: ①정리 ②우선순위 선정 ③마감 확인.
```

---

### 2) yongshin_explain
**facts_keys**
- `analysis.yongshin.{type,elements[],rationale.evidence[]}`
- `analysis.strength.bucket`

**light**
```
용신: {{analysis.yongshin.elements[0]}} 중심(유형: {{analysis.yongshin.type}}).
이유: {{analysis.yongshin.rationale.evidence[0]}} · {{analysis.yongshin.rationale.evidence[1]?}}
활용 팁: 관련 성질을 **습관/환경**으로 보완해 주세요.
```

**deep**
```
용신 해설(유형: {{analysis.yongshin.type}}):
핵심 오행: {{analysis.yongshin.elements}}.
근거:
- {{analysis.yongshin.rationale.evidence[0]}}
- {{analysis.yongshin.rationale.evidence[1]?}}
신강/신약: {{analysis.strength.bucket}} 경향에 따라 실천 강도를 조절하세요.
실천: 주간 루틴에 {{analysis.yongshin.elements[0]}} 성질을 반영한 **행동 2가지**를 고정합니다.
```

**pdf**
```
[용신 리포트]
유형: {{analysis.yongshin.type}} / 핵심 오행: {{analysis.yongshin.elements}}
판단 근거:
1) {{analysis.yongshin.rationale.evidence[0]}}
2) {{analysis.yongshin.rationale.evidence[1]?}}
코칭:
- 환경: 용신 성질을 지지하는 업무/공간 세팅
- 루틴: 주 {{analysis.yongshin.elements[0]}} 성질에 맞춘 체크리스트 고정
```

---

### 3) strength_explain
**facts_keys**
- `analysis.strength.{score,bucket,factors[]}`

**light**
```
신강/신약 요약: {{analysis.strength.bucket}} (점수 {{analysis.strength.score}}).
근거: {{analysis.strength.factors[0]}} · {{analysis.strength.factors[1]?}}
권장: **루틴 고정 + 기록**으로 과소/과다를 완화하세요.
```

**deep**
```
신강/신약 해석 — 점수 {{analysis.strength.score}}, 버킷 {{analysis.strength.bucket}}.
영향 요인:
- {{analysis.strength.factors[0]}}
- {{analysis.strength.factors[1]?}}
코칭:
- 집중: 하루 초반 고정 작업 블록 확보
- 보완: 주간 검토(15분)로 과부하/지연을 체크
```

**pdf**
```
[신강/신약 리포트]
지표: {{analysis.strength.score}}점 / 분류: {{analysis.strength.bucket}}
주요 요인: {{analysis.strength.factors}}
실행 전략:
- 스케줄: 우선순위 3개만 확정, 나머지 유예
- 체크: 주 1회 성과 로그 기록
```

---

### 4) decades_commentary
**facts_keys**
- `analysis.luck.decades.{start_age,direction,pillars[].{age,pillar,ten_god,stage}}`
- `analysis.yongshin.elements[]` (선택)

**light**
```
대운 시작: {{analysis.luck.decades.start_age}}세 ({{analysis.luck.decades.direction}}).
현재/다가오는 운의 키워드: {{analysis.luck.decades.pillars[0].ten_god}} 중심.
팁: **기록·정리·관계 조율** 같은 기본기를 유지하세요.
```

**deep**
```
대운 흐름(시작 {{analysis.luck.decades.start_age}}세, {{analysis.luck.decades.direction}}):
- 구간 A: {{analysis.luck.decades.pillars[0].age}}세 — {{analysis.luck.decades.pillars[0].ten_god}}/{{analysis.luck.decades.pillars[0].stage}}
- 구간 B: {{analysis.luck.decades.pillars[1].age}}세 — {{analysis.luck.decades.pillars[1].ten_god}}/{{analysis.luck.decades.pillars[1].stage}}
핵심: 변화 구간에는 **기록·정리·우선순위 재배치**가 유효합니다.
```

**pdf**
```
[대운 타임라인]
방향: {{analysis.luck.decades.direction}} / 시작연령: {{analysis.luck.decades.start_age}}세
구간 요약:
- {{analysis.luck.decades.pillars[0].age}}세: {{analysis.luck.decades.pillars[0].pillar}} ({{analysis.luck.decades.pillars[0].ten_god}}/{{analysis.luck.decades.pillars[0].stage}})
- {{analysis.luck.decades.pillars[1].age}}세: {{analysis.luck.decades.pillars[1].pillar}} ({{analysis.luck.decades.pillars[1].ten_god}}/{{analysis.luck.decades.pillars[1].stage}})
가이드: 큰 결정을 앞두고 **정보 수집→정리→검토** 순서를 지키세요.
```

---

### 5) annual_monthly_commentary
**facts_keys**
- 연: `analysis.luck.years.{YYYY}.{pillar,ten_god,stage?}`
- 월: `analysis.luck.months.{YYYY-MM}.{pillar,ten_god,stage?,term_window.{start,end}}`

**light**
```
이번 기간 포인트: 연 {{analysis.luck.years.Y.pillar}} / 월 {{analysis.luck.months.YM.pillar}}.
핵심 십성: {{analysis.luck.months.YM.ten_god}} 중심.
팁: 기간( {{analysis.luck.months.YM.term_window.start}} ~ {{analysis.luck.months.YM.term_window.end}} ) 동안 **정리·기록**에 시간을 고정하세요.
```

**deep**
```
연·월 포인트:
- 연: {{analysis.luck.years.Y.pillar}} ({{analysis.luck.years.Y.ten_god}}/{{analysis.luck.years.Y.stage?}})
- 월: {{analysis.luck.months.YM.pillar}} ({{analysis.luck.months.YM.ten_god}}/{{analysis.luck.months.YM.stage?}})
기간: {{analysis.luck.months.YM.term_window.start}} ~ {{analysis.luck.months.YM.term_window.end}}
코칭: 기간 초반 **계획 정비**, 중반 **실행 체크**, 후반 **정리/기록** 순으로 운영하세요.
```

**pdf**
```
[연·월운 리포트]
연간: {{analysis.luck.years.Y.pillar}} / 십성 {{analysis.luck.years.Y.ten_god}} / 단계 {{analysis.luck.years.Y.stage?}}
월간: {{analysis.luck.months.YM.pillar}} / 십성 {{analysis.luck.months.YM.ten_god}} / 단계 {{analysis.luck.months.YM.stage?}}
기간 창: {{analysis.luck.months.YM.term_window.start}} ~ {{analysis.luck.months.YM.term_window.end}}
운영 제안:
- 계획: 우선순위 3개 확정
- 실행: 주 2회 진행률 점검
- 정리: 기간 종료 전 마감 체크
```

---

## ACCEPTANCE CRITERIA
- 출력은 단일 JSON이며, `pack_id`/`lang`/`templates` 구조를 따른다.
- 각 토픽에 `facts_keys`와 `light`/`deep`/`pdf` 3개 본문이 존재한다.
- 본문은 KO-first, 사실 슬롯만 사용하며 금지사항(의료/법률/투자 구체조언, 임의 수치·날짜 생성)을 위반하지 않는다.
- 누락 값은 `{{MISSING(...)}}` 또는 조건 블록 생략으로 대응한다.
- 길이 한도: Light ≤300t, Deep ≤900t, PDF ≤1300t에 맞춰 간결하게 작성한다.

---

## NOW OUTPUT
위 스펙에 맞는 템플릿 팩 JSON을 그대로 출력하라. 불필요한 설명이나 주석은 금지.
