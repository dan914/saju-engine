"""
LLM Polish Service skeleton for 사주 앱 v1.4.

⚠️ WIP: This service is not production-ready

TODO:
- [ ] Add template-to-text polishing routes
- [ ] Integrate with LLM providers (Qwen Flash, DeepSeek, Gemini 2.5 Pro)
- [ ] Implement fallback chain (Qwen → DeepSeek → Gemini)
- [ ] Add token counting and rate limiting
- [ ] Add template validation
- [ ] Add comprehensive tests
- [ ] Add performance monitoring

Estimated effort: 6-8 hours to reach MVP status
See: services/llm-polish/README.md
"""

from __future__ import annotations

from services.common import create_service_app

APP_META = {
    "app": "saju-llm-polish",
    "version": "0.1.0-WIP",  # WIP marker
    "rule_id": "KR_classic_v1.4",
}

app = create_service_app(
    app_name=APP_META["app"],
    version=APP_META["version"],
    rule_id=APP_META["rule_id"],
)

# TODO: Add business logic routes
# @app.post("/polish/light")
# def polish_with_light_model(...): pass
#
# @app.post("/polish/deep")
# def polish_with_deep_model(...): pass
