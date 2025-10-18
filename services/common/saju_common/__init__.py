"""
Saju Common Package - Shared Interfaces and Implementations

Provides cross-service abstractions to avoid circular dependencies
and hyphened module name issues.

Public API:
- Protocols: TimeResolver, SolarTermLoader, DeltaTPolicy
- Implementations: BasicTimeResolver, TableSolarTermLoader, SimpleDeltaT
- Tables: SEASON_ELEMENT_BOOST, BRANCH_TO_SEASON, etc.
- Factories: get_default_*()

Version: 1.0.0
Date: 2025-10-09 KST

Usage:
    >>> from services.common.saju_common import BasicTimeResolver, TableSolarTermLoader
    >>> from services.common.saju_common import BRANCH_TO_SEASON
    >>>
    >>> # Use protocol-based dependencies
    >>> time_resolver = BasicTimeResolver()
    >>> utc_dt = time_resolver.to_utc(local_dt, "Asia/Seoul")
    >>>
    >>> # Access mapping tables
    >>> season = BRANCH_TO_SEASON["寅"]  # "spring"
"""

# Protocols
# Built-in implementations
from .builtins import (
    BasicTimeResolver,
    SimpleDeltaT,
    TableSolarTermLoader,
    get_default_delta_t_policy,
    get_default_solar_term_loader,
    get_default_time_resolver,
)

# File-based implementations
from .file_solar_term_loader import FileSolarTermLoader, SolarTermEntry
from .interfaces import DeltaTPolicy, SolarTermLoader, TimeResolver

# Mapping tables
from .seasons import (
    BRANCH_TO_ELEMENT,
    BRANCH_TO_SEASON,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATES,
    GREGORIAN_MONTH_TO_BRANCH,
    SEASON_ELEMENT_BOOST,
    STEM_TO_ELEMENT,
)

# Timezone handling
from .timezone_handler import (
    CITY_LMT_OFFSETS,
    DST_PERIODS,
    MODERN_LMT_OFFSETS,
    KoreanTimezoneHandler,
    TimezoneWarning,
    get_saju_adjusted_time,
)

__all__ = [
    # Protocols
    "TimeResolver",
    "SolarTermLoader",
    "DeltaTPolicy",
    # Implementations
    "BasicTimeResolver",
    "TableSolarTermLoader",
    "SimpleDeltaT",
    # File-based loaders
    "FileSolarTermLoader",
    "SolarTermEntry",
    # Factories
    "get_default_time_resolver",
    "get_default_solar_term_loader",
    "get_default_delta_t_policy",
    # Tables
    "GREGORIAN_MONTH_TO_BRANCH",
    "BRANCH_TO_SEASON",
    "BRANCH_TO_ELEMENT",
    "STEM_TO_ELEMENT",
    "SEASON_ELEMENT_BOOST",
    "ELEMENT_GENERATES",
    "ELEMENT_CONTROLS",
    # Timezone handling
    "KoreanTimezoneHandler",
    "get_saju_adjusted_time",
    "DST_PERIODS",
    "CITY_LMT_OFFSETS",
    "MODERN_LMT_OFFSETS",
    "TimezoneWarning",
]

__version__ = "1.0.0"
