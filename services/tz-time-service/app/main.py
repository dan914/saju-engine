"""Timezone conversion service."""

from __future__ import annotations

from saju_common import create_service_app

from .api import router
from .api.dependencies import preload_dependencies

APP_META = {
    "app": "saju-tz-time-service",
    "version": "0.1.0",
    "rule_id": "KR_classic_v1.4",
}

app = create_service_app(
    app_name=APP_META["app"],
    version=APP_META["version"],
    rule_id=APP_META["rule_id"],
)


@app.on_event("startup")
def _warm_singletons() -> None:
    """Preload heavy dependencies before serving requests."""
    preload_dependencies()


app.include_router(router, prefix="/v2")
