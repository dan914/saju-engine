"""
Common Service Interfaces (Protocols)

Defines protocol interfaces for cross-service dependencies:
- TimeResolver: Timezone conversions (UTC/LMT/local)
- SolarTermLoader: Solar term and season lookup
- DeltaTPolicy: ΔT (time correction) calculation

These protocols allow services to depend on abstractions rather than
concrete implementations, avoiding circular dependencies and hyphened
module name issues.

Version: 1.0.0
Date: 2025-10-09 KST
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class TimeResolver(Protocol):
    """
    Protocol for timezone conversions.

    Implementations must handle:
    - IANA timezone database (e.g., "Asia/Seoul")
    - UTC ↔ Local conversions
    - Optional: LMT (Local Mean Time) corrections
    """

    def to_utc(self, dt: datetime, tz: str) -> datetime:
        """
        Convert local datetime to UTC.

        Args:
            dt: Local datetime (naive or aware)
            tz: IANA timezone string (e.g., "Asia/Seoul")

        Returns:
            UTC datetime (aware)
        """
        ...

    def from_utc(self, dt: datetime, tz: str) -> datetime:
        """
        Convert UTC datetime to local timezone.

        Args:
            dt: UTC datetime (aware)
            tz: IANA timezone string

        Returns:
            Local datetime (aware)
        """
        ...


@runtime_checkable
class SolarTermLoader(Protocol):
    """
    Protocol for solar term and season lookup.

    Provides simplified access to:
    - Month branch (월지) determination
    - Season classification (spring/summer/long_summer/autumn/winter)

    Note: Full solar term calculation requires astronomical precision.
    Basic implementations may use Gregorian month approximations.
    """

    def month_branch(self, d: date) -> str:
        """
        Get Earth Branch for given date's month.

        Args:
            d: Date to query

        Returns:
            Earth Branch character (子丑寅卯辰巳午未申酉戌亥)

        Example:
            >>> loader.month_branch(date(2000, 2, 15))
            '寅'  # 인월 (立春 season)
        """
        ...

    def season(self, d: date) -> str:
        """
        Get season for given date.

        Args:
            d: Date to query

        Returns:
            Season string: "spring" | "summer" | "long_summer" | "autumn" | "winter"

        Note: "long_summer" (土旺 season) occurs 4 times per year:
        - 辰月 (spring → summer transition)
        - 未月 (summer → autumn transition)
        - 戌月 (autumn → winter transition)
        - 丑月 (winter → spring transition)
        """
        ...


@runtime_checkable
class DeltaTPolicy(Protocol):
    """
    Protocol for ΔT (time correction) calculation.

    ΔT represents the difference between:
    - TT (Terrestrial Time, uniform atomic time)
    - UT1 (Universal Time, Earth rotation based)

    Required for historical date calculations (e.g., solar term before 1900).
    Modern dates (post-2000) have ΔT ≈ 69 seconds.

    Reference: https://eclipse.gsfc.nasa.gov/SEcat5/deltat.html
    """

    def delta_t_seconds(self, year: int, month: int) -> float:
        """
        Calculate ΔT in seconds for given year/month.

        Args:
            year: Calendar year (Gregorian)
            month: Month (1-12)

        Returns:
            ΔT in seconds (typically 0-100 for 1900-2100)

        Example:
            >>> policy.delta_t_seconds(2000, 1)
            63.8  # Approximate
            >>> policy.delta_t_seconds(2025, 1)
            69.5  # Approximate
        """
        ...
