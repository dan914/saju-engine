# LLM Polish Service - WIP

**Status:** ⚠️ Work In Progress - Not Production Ready

**Version:** 0.1.0-WIP

**Estimated Effort to MVP:** 6-8 hours

---

## Current State

This service is a FastAPI skeleton that provides the basic health check endpoint via `create_service_app()` from `services.common`. It does **NOT** currently implement any LLM integration or text polishing logic.

**What Works:**
- Health check endpoint (via common service app)
- Basic FastAPI application structure
- Service metadata (app name, version, rule_id)

**What's Missing:**
- LLM provider integrations (Qwen, DeepSeek, Gemini, GPT-5)
- Fallback chain logic
- Template-to-text polishing
- Token counting and rate limiting
- Template validation
- Comprehensive tests
- Performance monitoring

---

## What This Service Should Do

The LLM Polish Service transforms structured analysis results into natural Korean language. It should:

1. **Light Polishing (Free, 3/day):**
   - Use Qwen Flash (primary) → DeepSeek (fallback) → Gemini 2.5 Pro (final fallback)
   - Fast responses (< 5 seconds)
   - Simple questions and summaries
   - No token consumption

2. **Deep Polishing (Token-based):**
   - Use Gemini 2.5 Pro (primary) → GPT-5 (backstop)
   - High-quality long-form content
   - Detailed interpretations and coaching
   - Consumes 1 token per request

3. **Template Processing:**
   - Load policy-based templates
   - Fill in placeholders with analysis data
   - Validate template variables
   - Return structured JSON responses

4. **Error Handling:**
   - Retry with exponential backoff
   - Fallback to next provider on failure
   - Return partial results if possible
   - Log all failures for monitoring

---

## TODO Checklist

- [ ] Add template-to-text polishing routes (`/polish/light`, `/polish/deep`)
- [ ] Integrate with Qwen Flash (Light primary)
- [ ] Integrate with DeepSeek-Chat (Light fallback)
- [ ] Integrate with Gemini 2.5 Pro (Light final fallback + Deep primary)
- [ ] Integrate with GPT-5 (Deep backstop)
- [ ] Implement fallback chain logic with retries
- [ ] Add token counting (input + output)
- [ ] Add rate limiting (Light: 3/day, Deep: token-based)
- [ ] Add template validation (check required fields)
- [ ] Add comprehensive tests (unit + integration + load)
- [ ] Add performance monitoring (latency, token usage, errors)
- [ ] Add request/response logging
- [ ] Add LLM Guard integration (pre/post validation)
- [ ] Add streaming support for long responses
- [ ] Add caching for common templates

---

## Implementation Notes

### Example: Light Polish Route

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from typing import Literal

router = APIRouter(tags=["polish"])

class PolishRequest(BaseModel):
    template_id: str
    variables: dict
    user_id: str

class PolishResponse(BaseModel):
    text: str
    model: str
    tokens_used: int
    latency_ms: int

@router.post("/polish/light", response_model=PolishResponse)
async def polish_light(request: PolishRequest):
    """Polish text using light models (free, 3/day)."""
    # Try Qwen Flash first
    try:
        return await _polish_with_qwen(request)
    except Exception as e:
        print(f"Qwen failed: {e}, trying DeepSeek...")

    # Fallback to DeepSeek
    try:
        return await _polish_with_deepseek(request)
    except Exception as e:
        print(f"DeepSeek failed: {e}, trying Gemini...")

    # Final fallback to Gemini
    try:
        return await _polish_with_gemini(request)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"All light models failed: {str(e)}"
        )

async def _polish_with_qwen(request: PolishRequest) -> PolishResponse:
    """Call Qwen Flash API."""
    # Load template
    template = load_template(request.template_id)
    prompt = template.format(**request.variables)

    # Call Qwen API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.qwen.ai/v1/chat/completions",
            json={
                "model": "qwen-flash",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
            headers={"Authorization": f"Bearer {QWEN_API_KEY}"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        return PolishResponse(
            text=data["choices"][0]["message"]["content"],
            model="qwen-flash",
            tokens_used=data["usage"]["total_tokens"],
            latency_ms=int(response.elapsed.total_seconds() * 1000),
        )
```

### Example: Deep Polish Route

```python
@router.post("/polish/deep", response_model=PolishResponse)
async def polish_deep(request: PolishRequest):
    """Polish text using deep models (token-based)."""
    # Check token balance
    tokens_left = await check_token_balance(request.user_id)
    if tokens_left < 1:
        raise HTTPException(
            status_code=402,
            detail="Insufficient tokens. Watch ads to earn more."
        )

    # Try Gemini 2.5 Pro first
    try:
        result = await _polish_with_gemini_pro(request)
        await consume_token(request.user_id, 1)
        return result
    except Exception as e:
        print(f"Gemini failed: {e}, trying GPT-5...")

    # Backstop to GPT-5
    try:
        result = await _polish_with_gpt5(request)
        await consume_token(request.user_id, 1)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"All deep models failed: {str(e)}"
        )
```

### Example: Template Validation

```python
def load_template(template_id: str) -> str:
    """Load template from policy file and validate."""
    templates = {
        "strength_analysis": "일간 {day_stem}은(는) {season} 계절에 {strength_level} 상태입니다...",
        "luck_flow": "현재 {current_age}세, {luck_direction} 대운 중입니다...",
        # ... more templates
    }

    if template_id not in templates:
        raise ValueError(f"Unknown template_id: {template_id}")

    return templates[template_id]

def validate_template_variables(template: str, variables: dict):
    """Ensure all required variables are provided."""
    import re
    required = set(re.findall(r'\{(\w+)\}', template))
    provided = set(variables.keys())
    missing = required - provided

    if missing:
        raise ValueError(f"Missing template variables: {missing}")
```

### Example: LLM Guard Integration

```python
from app.guard import LLMGuard

guard = LLMGuard.from_file("policy/llm_guard_policy_v1.1.json")

async def _polish_with_guard(request: PolishRequest, model_fn):
    """Wrap LLM call with pre/post validation."""
    # Pre-generation check
    pre_verdict = guard.validate_pre(
        template_id=request.template_id,
        variables=request.variables,
    )
    if pre_verdict["verdict"] == "block":
        raise HTTPException(status_code=400, detail=pre_verdict["reason"])

    # Generate
    result = await model_fn(request)

    # Post-generation check
    post_verdict = guard.validate_post(
        generated_text=result.text,
        template_id=request.template_id,
        variables=request.variables,
    )
    if post_verdict["verdict"] == "block":
        raise HTTPException(status_code=500, detail=post_verdict["reason"])
    elif post_verdict["verdict"] == "revise":
        # Re-generate with stricter constraints
        result = await model_fn(request, temperature=0.3)

    return result
```

---

## Model Routing Policy

### Light Models (Free, 3/day)

| Priority | Model | Use Case | Timeout | Fallback |
|----------|-------|----------|---------|----------|
| 1st | Qwen Flash | Default | 10s | DeepSeek |
| 2nd | DeepSeek-Chat | Qwen failure | 15s | Gemini |
| 3rd | Gemini 2.5 Pro | Both failed | 20s | Error |

### Deep Models (1 token/request)

| Priority | Model | Use Case | Timeout | Fallback |
|----------|-------|----------|---------|----------|
| 1st | Gemini 2.5 Pro | Default | 30s | GPT-5 |
| 2nd | GPT-5 | Gemini failure | 45s | Error |

---

## Testing Strategy

1. **Unit Tests:**
   - Test template loading/validation
   - Mock LLM API calls
   - Verify fallback chain logic
   - Test error handling

2. **Integration Tests:**
   - Call real LLM APIs (dev environment)
   - Verify token counting
   - Test rate limiting
   - Verify LLM Guard integration

3. **Load Tests:**
   - Simulate concurrent requests
   - Measure P50/P95/P99 latency
   - Verify fallback under load
   - Test rate limiting behavior

4. **Quality Tests:**
   - Verify Korean output quality
   - Check for prohibited content
   - Validate against policy constraints
   - Test template variable injection

---

## Dependencies

**Required Services:**
- LLM Guard service (for pre/post validation)
- Redis (for rate limiting + caching)
- Token service (for balance checking)

**Python Packages:**
- fastapi
- httpx (async HTTP client)
- openai (for GPT-5)
- google-generativeai (for Gemini)
- tiktoken (token counting)
- jinja2 (template rendering)
- pydantic

**External APIs:**
- Qwen AI API (primary light)
- DeepSeek API (fallback light)
- Google Gemini API (fallback light + primary deep)
- OpenAI GPT-5 API (backstop deep)

---

## Next Steps

1. Implement Qwen Flash integration (1.5 hours)
2. Implement DeepSeek integration (1.5 hours)
3. Implement Gemini 2.5 Pro integration (1.5 hours)
4. Implement GPT-5 integration (1 hour)
5. Add fallback chain logic (1 hour)
6. Add template system (1 hour)
7. Add LLM Guard integration (1.5 hours)
8. Add comprehensive tests (2 hours)
9. Add performance monitoring (1 hour)

**Total Estimated Effort:** 6-8 hours
