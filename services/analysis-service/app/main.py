"""Ten gods & relations analysis service."""
from __future__ import annotations

from services.common import create_service_app

from .api import router

APP_META = {
    "app": "saju-analysis-service",
    "version": "0.1.0",
    "rule_id": "KR_classic_v1.4",
}

app = create_service_app(
    app_name=APP_META["app"],
    version=APP_META["version"],
    rule_id=APP_META["rule_id"],
)
app.include_router(router, prefix="/v2")
