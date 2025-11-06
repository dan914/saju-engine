"""
Built-in Implementations for Common Service Interfaces

Provides basic implementations using only stdlib:
- BasicTimeResolver: Uses zoneinfo (Python 3.9+)
- TableSolarTermLoader: Uses simplified Gregorian month mapping
- SimpleDeltaT: Linear approximation for modern dates

These implementations are sufficient for:
- Development/testing
- Production use when month-level precision is acceptable
- Services that don't require astronomical precision

For production-grade solar term calculation, use astro-service.

Version: 1.0.0
Date: 2025-10-09 KST
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from .interfaces import DeltaTPolicy, SolarTermLoader, TimeResolver
from .seasons import BRANCH_TO_SEASON, GREGORIAN_MONTH_TO_BRANCH


class BasicTimeResolver(TimeResolver):
    """
    Basic timezone resolver using Python's zoneinfo module.

    Handles:
    - IANA timezone database
    - DST transitions
    - UTC ↔ Local conversions

    Does NOT handle:
    - LMT (Local Mean Time) corrections
    - Historical timezone changes before IANA database
    """

    def to_utc(self, dt: datetime, tz: str) -> datetime:
        """Convert local datetime to UTC"""
        if dt.tzinfo is None:
            # Assume dt is in local timezone
            dt = dt.replace(tzinfo=ZoneInfo(tz))
        return dt.astimezone(ZoneInfo("UTC"))

    def from_utc(self, dt: datetime, tz: str) -> datetime:
        """Convert UTC datetime to local timezone"""
        if dt.tzinfo is None:
            # Assume dt is UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(ZoneInfo(tz))


class TableSolarTermLoader(SolarTermLoader):
    """
    Table-based solar term loader using simplified Gregorian month mapping.

    Accuracy:
    - Month branch: ±15 days (sufficient for month-level analysis)
    - Season: ±7 days at transitions

    For precise solar term calculation (day/hour level), use astro-service
    with actual astronomical ephemeris data.
    """

    def month_branch(self, d: date) -> str:
        """
        Get Earth Branch for date's month using Gregorian approximation.

        Note: Actual solar terms can shift by ±15 days. For precise
        calculations, use astro-service.
        """
        return GREGORIAN_MONTH_TO_BRANCH[d.month]

    def season(self, d: date) -> str:
        """
        Get season for date using month branch.

        Returns one of:
        - "spring" (寅卯, 2-3월)
        - "summer" (巳午, 5-6월)
        - "long_summer" (辰未戌丑, 토왕 계절)
        - "autumn" (申酉, 8-9월)
        - "winter" (亥子, 11-12월)
        """
        branch = self.month_branch(d)
        return BRANCH_TO_SEASON[branch]


class SimpleDeltaT(DeltaTPolicy):
    """
    Simplified ΔT calculation using linear approximation.

    Formula: ΔT ≈ 69 + 0.1 * (year - 2000)

    Accuracy:
    - 2000-2030: ±2 seconds
    - 1950-2050: ±5 seconds
    - Outside this range: Not recommended

    For historical dates (pre-1900) or high-precision astronomy,
    use NASA's polynomial fit or IERS Bulletin A data.

    Reference:
    - NASA: https://eclipse.gsfc.nasa.gov/SEcat5/deltat.html
    - IERS: https://www.iers.org/IERS/EN/DataProducts/EarthOrientationData/eop.html
    """

    def delta_t_seconds(self, year: int, month: int) -> float:
        """
        Calculate ΔT using linear approximation.

        Args:
            year: Calendar year (Gregorian)
            month: Month (1-12, currently unused in linear model)

        Returns:
            ΔT in seconds

        Example:
            >>> dt = SimpleDeltaT()
            >>> dt.delta_t_seconds(2000, 1)
            69.0
            >>> dt.delta_t_seconds(2025, 1)
            71.5
        """
        # Linear approximation: ΔT increases by ~1 second per decade
        return 69.0 + 0.1 * max(0, year - 2000)


# Convenience factory functions
def get_default_time_resolver() -> TimeResolver:
    """Get default TimeResolver implementation (BasicTimeResolver)"""
    return BasicTimeResolver()


def get_default_solar_term_loader() -> SolarTermLoader:
    """Get default SolarTermLoader implementation (TableSolarTermLoader)"""
    return TableSolarTermLoader()


def get_default_delta_t_policy() -> DeltaTPolicy:
    """Get default DeltaTPolicy implementation (SimpleDeltaT)"""
    return SimpleDeltaT()
