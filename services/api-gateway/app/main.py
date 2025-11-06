"""
API Gateway skeleton for 사주 앱 v1.4.

⚠️ WIP: This service is not production-ready

TODO:
- [ ] Add routing to analysis-service
- [ ] Add routing to llm-polish
- [ ] Add authentication/authorization middleware
- [ ] Add rate limiting
- [ ] Add request/response logging
- [ ] Add comprehensive tests
- [ ] Add API documentation

Estimated effort: 4-6 hours to reach MVP status
See: services/api-gateway/README.md
"""

from __future__ import annotations

from saju_common import create_service_app

APP_META = {
    "app": "saju-api-gateway",
    "version": "0.1.0-WIP",  # WIP marker
    "rule_id": "KR_classic_v1.4",
}

app = create_service_app(
    app_name=APP_META["app"],
    version=APP_META["version"],
    rule_id=APP_META["rule_id"],
)

# TODO: Add business logic routes
# @app.post("/analyze")
# def route_to_analysis_service(...): pass
#
# @app.post("/chat/send")
# def route_to_llm_polish(...): pass
