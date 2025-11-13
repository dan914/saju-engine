# -*- coding: utf-8 -*-
"""
Entitlement Service Configuration
Pydantic settings with environment variable support
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    # Service metadata
    app_name: str = "entitlement-service"
    version: str = "1.0.0"
    environment: str = Field(default="development", description="Environment: development|staging|production")

    # Database configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/entitlements",
        description="PostgreSQL connection URL (async driver)"
    )

    # Redis configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for rate limiting and caching"
    )

    # Firebase JWT configuration
    jwt_audience: str = Field(
        default="your-firebase-project",
        description="Firebase project ID for JWT audience validation"
    )
    jwt_issuer: str = Field(
        default="https://securetoken.google.com/your-firebase-project",
        description="Firebase token issuer URL"
    )
    firebase_jwks_url: str = Field(
        default="https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com",
        description="Firebase JWKS endpoint",
    )
    firebase_jwks_cache_seconds: int = Field(
        default=3600,
        description="How long to cache JWKS entries",
    )
    jwt_clock_skew_seconds: int = Field(
        default=60,
        description="Allowed clock skew when verifying JWTs",
    )
    auth_debug_header_enabled: bool = Field(
        default=False,
        description="Allow X-Debug-User overrides (development only)",
    )
    admin_role_claim: str = Field(
        default="roles",
        description="JWT claim that stores user roles",
    )
    admin_role_value: str = Field(
        default="admin",
        description="Role required to access admin endpoints",
    )

    # Rate limiting (requests per minute)
    rate_limit_consume_rpm: int = Field(default=10, description="Consume endpoint rate limit (per user)")
    rate_limit_reward_rpm: int = Field(default=3, description="Reward endpoint rate limit (per user)")
    rate_limit_entitlements_rpm: int = Field(default=60, description="Entitlements fetch rate limit (per user)")

    # Ad reward configuration
    ad_cooldown_seconds: int = Field(default=3600, description="Cooldown between ad rewards (1 hour)")
    ad_daily_cap: int = Field(default=2, description="Maximum ad rewards per day (KST)")
    ad_monthly_cap: int = Field(default=60, description="Maximum ad rewards per month")
    ad_reward_expiry_minutes: int = Field(default=5, description="SSV pending reward expiry time")

    # Timezone and scheduling
    timezone: str = Field(default="Asia/Seoul", description="Application timezone (KST)")

    # Observability
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    log_level: str = Field(default="INFO", description="Logging level: DEBUG|INFO|WARNING|ERROR")

    # Security
    idempotency_ttl_hours: int = Field(default=24, description="Idempotency key TTL in hours")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
