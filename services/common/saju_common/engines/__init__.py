"""Shared analysis engines for saju services.

This package contains core calculation engines extracted from analysis-service
to be shared across multiple services (pillars-service, analysis-service, etc.).

Architecture Decision:
- Code-level sharing via common package (not runtime HTTP calls)
- Pure logic/data/policy engines only (no HTTP/DB access)
- Maintains same function signatures as original implementations
"""

from .annual import AnnualLuckCalculator, ChartContext, EngineOptions, LuckFrame, DEFAULT_ENGINE_OPTIONS
from .daily import DailyLuckCalculator
from .luck import LuckCalculator, LuckContext
from .monthly import MonthlyLuckCalculator
from .policy_config import LuckPolicyBundle, LuckPolicyConfig, load_luck_policy, load_luck_policy_bundle
from .school import SchoolProfileManager
from .shensha import ShenshaCatalog

__all__ = [
    "AnnualLuckCalculator",
    "DailyLuckCalculator",
    "EngineOptions",
    "DEFAULT_ENGINE_OPTIONS",
    "ChartContext",
    "LuckFrame",
    "MonthlyLuckCalculator",
    "LuckPolicyConfig",
    "LuckPolicyBundle",
    "load_luck_policy",
    "load_luck_policy_bundle",
    "LuckCalculator",
    "LuckContext",
    "ShenshaCatalog",
    "SchoolProfileManager",
]
