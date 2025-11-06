"""Locust scenario exercising the atomic Redis rate limiter."""

import json
import os
from typing import Any

from locust import HttpUser, between, task


class _ScenarioConfig:
    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.rate_limit_key = os.getenv("RATE_LIMIT_KEY", "user:loadtest")
        self.token_cost = int(os.getenv("TOKEN_COST", "1"))
        self.use_atomic_flag = os.getenv("USE_ATOMIC_FLAG", "false").lower() in {
            "1",
            "true",
            "yes",
        }


CONFIG = _ScenarioConfig()


class RateLimitUser(HttpUser):
    wait_time = between(0.1, 0.3)

    def on_start(self) -> None:
        self.client.headers.update({
            "X-RateLimit-Test-Key": CONFIG.rate_limit_key,
            "X-RateLimit-Cost": str(CONFIG.token_cost),
        })
        if CONFIG.use_atomic_flag:
            self.client.headers["X-Enable-Atomic-RateLimit"] = "true"

    @task
    def hit_rate_limited_endpoint(self) -> None:
        response = self.client.get(
            "/internal/rate-limit/probe",
            name="rate-limit-probe",
            timeout=5,
        )
        meta: dict[str, Any] = {
            "status": response.status_code,
            "remaining": response.headers.get("X-RateLimit-Remaining"),
            "retry_after": response.headers.get("Retry-After"),
        }
        self.environment.events.request.fire(
            request_type="CUSTOM",
            name="token_bucket",
            response_time=response.elapsed.total_seconds() * 1000,
            response_length=len(response.content),
            response=response,
            exception=None,
            context=json.dumps(meta),
        )


class RateLimitNoise(HttpUser):
    wait_time = between(0.2, 0.6)

    @task
    def out_of_band_requests(self) -> None:
        self.client.get("/health", name="healthcheck", timeout=5)
