"""LLM checker service."""
from __future__ import annotations

from services.common import create_service_app

APP_META = {
    "app": "saju-llm-checker",
    "version": "0.1.0",
    "rule_id": "KR_classic_v1.4",
}

app = create_service_app(
    app_name=APP_META["app"],
    version=APP_META["version"],
    rule_id=APP_META["rule_id"],
)
