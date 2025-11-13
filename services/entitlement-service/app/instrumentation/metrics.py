# -*- coding: utf-8 -*-
"""
Prometheus Metrics for Entitlement Service
8 core metrics for observability
"""

from prometheus_client import Counter, Histogram, Gauge


# Token consumption metrics
token_consume_total = Counter(
    "saju_tokens_consumed_total",
    "Total tokens consumed by users",
    ["action", "plan", "idempotent"]
)
# Labels:
# - action: "deep_chat"|"pdf_report"
# - plan: "free"|"plus"|"pro"
# - idempotent: "true"|"false"

token_consume_errors = Counter(
    "saju_token_consume_errors_total",
    "Token consumption errors",
    ["error_code"]
)
# Labels:
# - error_code: "INSUFFICIENT"|"OPTIMISTIC_LOCK"|"RATE_LIMIT"|"VALIDATION"

# Ad reward metrics
ad_reward_total = Counter(
    "saju_ad_rewards_total",
    "Ad rewards processed",
    ["status"]
)
# Labels:
# - status: "verified"|"rejected"|"cooldown"|"daily_cap"|"monthly_cap"

ad_reward_fraud = Counter(
    "saju_ad_reward_fraud_total",
    "Ad reward fraud detections",
    ["reason"]
)
# Labels:
# - reason: "rapid_ad_views"|"ip_hopping"|"device_mismatch"|"unusual_timing"

# Quota reset metrics
daily_quota_reset_total = Counter(
    "saju_daily_quota_resets_total",
    "Daily quota resets (00:00 KST)"
)

monthly_quota_reset_total = Counter(
    "saju_monthly_quota_resets_total",
    "Monthly quota resets (plan renewal)"
)

# Latency metrics
token_consume_duration = Histogram(
    "saju_token_consume_duration_seconds",
    "Token consumption latency (seconds)",
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
)

entitlement_fetch_duration = Histogram(
    "saju_entitlement_fetch_duration_seconds",
    "Entitlement fetch latency (seconds)",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.2, 0.5]
)

# Token bucket gauges (for monitoring)
token_buckets_gauge = Gauge(
    "saju_token_buckets",
    "Current token bucket levels",
    ["user_tier", "bucket_type"]
)
# Labels:
# - user_tier: "free"|"plus"|"pro"
# - bucket_type: "plan"|"earned"|"bonus"
