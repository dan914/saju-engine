# -*- coding: utf-8 -*-
"""Core business logic services for entitlement management."""

from .token_service import (
    consume_tokens_once,
    OptimisticLockError,
    InsufficientTokensError,
    compute_bucket_draw,
)
from .quota_service import (
    lazy_daily_reset_if_needed,
    monthly_plan_reset_if_due,
)
from .ssv_verifier import (
    verify_admob_ssv,
    ssv_request_hash,
    fetch_keys,
)
from .fraud_detector import (
    detect_fraud,
    FraudDecision,
)

__all__ = [
    "consume_tokens_once",
    "OptimisticLockError",
    "InsufficientTokensError",
    "compute_bucket_draw",
    "lazy_daily_reset_if_needed",
    "monthly_plan_reset_if_due",
    "verify_admob_ssv",
    "ssv_request_hash",
    "fetch_keys",
    "detect_fraud",
    "FraudDecision",
]
