"""
LLM Guard/Checker Service skeleton for 사주 앱 v1.4.

⚠️ WIP: This service is not production-ready

TODO:
- [ ] Add LLM Guard v1.1 pre-generation validation routes
- [ ] Add post-generation validation routes
- [ ] Implement 6 guard families (DETERMINISM, TRACE_INTEGRITY, etc.)
- [ ] Add verdict logic (allow/block/revise)
- [ ] Add comprehensive tests
- [ ] Add policy loader for llm_guard_policy_v1.1.json

Estimated effort: 4-6 hours to reach MVP status
See: services/llm-checker/README.md and LLM_GUARD_V1_ANALYSIS_AND_PLAN.md
"""

from __future__ import annotations

from services.common import create_service_app

APP_META = {
    "app": "saju-llm-checker",
    "version": "0.1.0-WIP",  # WIP marker
    "rule_id": "KR_classic_v1.4",
}

app = create_service_app(
    app_name=APP_META["app"],
    version=APP_META["version"],
    rule_id=APP_META["rule_id"],
)

# TODO: Add business logic routes
# @app.post("/guard/pre")
# def validate_before_llm_call(...): pass
#
# @app.post("/guard/post")
# def validate_after_llm_call(...): pass
