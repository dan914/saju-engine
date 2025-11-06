"""
Korean Timezone Handler with Historical DST and Timezone Changes

Handles:
- DST (Summer Time) periods: 1948-1960, 1987-1988
- Historical timezone changes: 1908, 1912, 1954, 1961
- North Korean timezone changes: 2015-2018
- City-specific LMT offsets (pre-1908)
- DST gap/overlap time detection

Based on:
- IANA TZDB Asia/Seoul
- Korean government records (관보)
- National Archives of Korea
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# DST (Summer Time) periods in Korea
DST_PERIODS = [
    # 1948-1960 periods
    {"start": datetime(1948, 6, 1, 0, 0), "end": datetime(1948, 9, 13, 0, 0)},
    {"start": datetime(1949, 4, 3, 0, 0), "end": datetime(1949, 9, 11, 0, 0)},
    {"start": datetime(1950, 4, 1, 0, 0), "end": datetime(1950, 9, 10, 0, 0)},
    {"start": datetime(1951, 5, 6, 0, 0), "end": datetime(1951, 9, 9, 0, 0)},
    {"start": datetime(1955, 5, 5, 0, 0), "end": datetime(1955, 9, 9, 0, 0)},
    {"start": datetime(1956, 5, 20, 0, 0), "end": datetime(1956, 9, 30, 0, 0)},
    {"start": datetime(1957, 5, 5, 0, 0), "end": datetime(1957, 9, 22, 0, 0)},
    {"start": datetime(1958, 5, 4, 0, 0), "end": datetime(1958, 9, 21, 0, 0)},
    {"start": datetime(1959, 5, 3, 0, 0), "end": datetime(1959, 9, 20, 0, 0)},
    {"start": datetime(1960, 5, 1, 0, 0), "end": datetime(1960, 9, 18, 0, 0)},
    # 1987-1988 Olympic periods (precise times: 02:00 start, 03:00 end)
    {"start": datetime(1987, 5, 10, 2, 0), "end": datetime(1987, 10, 11, 3, 0)},
    {"start": datetime(1988, 5, 8, 2, 0), "end": datetime(1988, 10, 9, 3, 0)},
]

# City-specific LMT offsets (minutes from UTC, pre-1908)
# Based on geographical longitude
CITY_LMT_OFFSETS = {
    "Seoul": 507.8,  # 126.978°E → UTC+8:27:52
    "Busan": 516.3,  # 129.075°E → UTC+8:36:18
    "Incheon": 506.8,  # 126.711°E → UTC+8:26:48
    "Daegu": 514.4,  # 128.601°E → UTC+8:34:24
    "Daejeon": 509.5,  # 127.385°E → UTC+8:29:30
    "Gwangju": 506.6,  # 126.916°E → UTC+8:26:36
    "Pyongyang": 503.0,  # 125.754°E → UTC+8:23:00
}

# Modern LMT offsets (minutes from standard meridian, post-1908)
# These are used for traditional saju calculations
MODERN_LMT_OFFSETS = {
    "Asia/Seoul": -32,  # 126.978°E vs 135°E
    "Asia/Busan": -24,  # 129.075°E vs 135°E
    "Asia/Incheon": -32,  # 126.711°E vs 135°E (same as Seoul)
    "Asia/Daegu": -27,  # 128.601°E vs 135°E
    "Asia/Daejeon": -31,  # 127.385°E vs 135°E
    "Asia/Gwangju": -32,  # 126.916°E vs 135°E (same as Seoul)
    "Asia/Pyongyang": -34,  # 125.754°E vs 127.5°E (NK standard)
}


class TimezoneWarning:
    """Warning flags for timezone edge cases."""

    DST_GAP = "DST_GAP"  # Non-existent time (skipped)
    DST_OVERLAP = "DST_OVERLAP"  # Ambiguous time (repeated)
    DELTA_T_BOUNDARY = "DELTA_T"  # Near solar term boundary
    HISTORICAL_LMT = "HIST_LMT"  # Pre-1908 LMT uncertainty


class KoreanTimezoneHandler:
    """Handle Korean timezone complexities for saju calculations."""

    def __init__(self):
        self.warnings = []

    def is_dst_period(self, dt: datetime) -> bool:
        """Check if datetime falls within DST period."""
        for period in DST_PERIODS:
            if period["start"] <= dt < period["end"]:
                return True
        return False

    def is_dst_gap(self, dt: datetime) -> Tuple[bool, Optional[str]]:
        """
        Check if time falls in DST gap (non-existent hour).

        Returns:
            (is_gap, message)
        """
        # 1987-1988: 02:00-02:59:59 doesn't exist on start date
        gap_periods = [
            (datetime(1987, 5, 10, 2, 0), datetime(1987, 5, 10, 3, 0)),
            (datetime(1988, 5, 8, 2, 0), datetime(1988, 5, 8, 3, 0)),
        ]

        for start, end in gap_periods:
            if start <= dt < end:
                return (
                    True,
                    f"Time {dt.strftime('%H:%M')} doesn't exist (DST gap, clocks moved forward)",
                )

        return False, None

    def is_dst_overlap(self, dt: datetime) -> Tuple[bool, Optional[str]]:
        """
        Check if time falls in DST overlap (ambiguous hour).

        Returns:
            (is_overlap, message)
        """
        # 1987-1988: 02:00-02:59:59 repeats on end date
        overlap_periods = [
            (datetime(1987, 10, 11, 2, 0), datetime(1987, 10, 11, 3, 0)),
            (datetime(1988, 10, 9, 2, 0), datetime(1988, 10, 9, 3, 0)),
        ]

        for start, end in overlap_periods:
            if start <= dt < end:
                return (
                    True,
                    f"Time {dt.strftime('%H:%M')} occurs twice (DST overlap, using standard time)",
                )

        return False, None

    def get_standard_time_offset(self, dt: datetime, location: str = "Seoul") -> int:
        """
        Get standard time offset (hours) for given datetime and location.

        Historical changes:
        - Before 1908: LMT (varies by city)
        - 1908-1912: UTC+8:30
        - 1912-1954: UTC+9:00
        - 1954-1961 (South): UTC+8:30
        - 1961-present (South): UTC+9:00
        - 2015-2018 (North): UTC+8:30
        - 2018-present (North): UTC+9:00
        """
        # North Korea special handling
        if "Pyongyang" in location:
            if datetime(2015, 8, 15) <= dt < datetime(2018, 5, 5):
                return 8.5  # Pyongyang Time
            return 9.0

        # South Korea timeline
        if dt < datetime(1908, 4, 1):
            # Pre-1908: Use city-specific LMT
            return CITY_LMT_OFFSETS.get(location, 507.8) / 60.0  # Default Seoul

        elif dt < datetime(1912, 1, 1):
            # 1908-1912: UTC+8:30
            return 8.5

        elif dt < datetime(1954, 3, 21):
            # 1912-1954: UTC+9:00
            return 9.0

        elif dt < datetime(1961, 8, 10):
            # 1954-1961 (South Korea only): UTC+8:30
            return 8.5

        else:
            # 1961-present: UTC+9:00
            return 9.0

    def apply_dst_adjustment(self, dt: datetime) -> Tuple[datetime, bool]:
        """
        Apply DST adjustment if applicable.

        Returns:
            (adjusted_datetime, dst_applied)
        """
        if self.is_dst_period(dt):
            # During DST, subtract 1 hour to get standard time
            return dt - timedelta(hours=1), True
        return dt, False

    def get_lmt_offset(self, location: str, dt: datetime) -> int:
        """
        Get LMT offset in minutes for saju calculation.

        Args:
            location: City name or timezone string
            dt: Datetime (for historical context)

        Returns:
            Offset in minutes from standard meridian
        """
        # Pre-1908: Use historical LMT
        if dt < datetime(1908, 4, 1):
            city = location.split(",")[0].strip() if "," in location else location
            city = city.replace("Asia/", "")
            lmt_minutes = CITY_LMT_OFFSETS.get(city, 507.8)
            # Convert to offset from UTC
            return int(lmt_minutes - 540)  # 540 = 9 hours * 60

        # Post-1908: Use modern LMT offsets for saju
        if location.startswith("Asia/"):
            return MODERN_LMT_OFFSETS.get(location, -32)

        # Try to match city name
        city = location.split(",")[0].strip()
        tz_name = f"Asia/{city}"
        return MODERN_LMT_OFFSETS.get(tz_name, -32)

    def convert_to_saju_time(
        self,
        birth_dt: datetime,
        location: str = "Seoul",
        apply_dst: bool = True,
        apply_lmt: bool = True,
    ) -> Dict:
        """
        Convert birth datetime to saju calculation time.

        This is the main entry point for timezone handling.

        Args:
            birth_dt: Birth datetime in local timezone
            location: City name or timezone
            apply_dst: Whether to apply DST correction
            apply_lmt: Whether to apply LMT correction

        Returns:
            Dict with:
            - adjusted_time: Adjusted datetime for calculation
            - dst_applied: Whether DST was applied
            - lmt_offset: LMT offset used (minutes)
            - warnings: List of warning messages
            - metadata: Additional context
        """
        self.warnings = []
        result = {
            "original_time": birth_dt,
            "adjusted_time": birth_dt,
            "dst_applied": False,
            "lmt_offset": 0,
            "warnings": [],
            "metadata": {},
        }

        # Check for DST gap/overlap
        is_gap, gap_msg = self.is_dst_gap(birth_dt)
        if is_gap:
            self.warnings.append({"type": TimezoneWarning.DST_GAP, "message": gap_msg})
            # Auto-correct: move forward 1 hour
            birth_dt = birth_dt + timedelta(hours=1)
            result["metadata"]["dst_gap_corrected"] = True

        is_overlap, overlap_msg = self.is_dst_overlap(birth_dt)
        if is_overlap:
            self.warnings.append({"type": TimezoneWarning.DST_OVERLAP, "message": overlap_msg})
            result["metadata"]["dst_overlap"] = True

        # Step 1: Apply DST if applicable
        if apply_dst:
            adjusted, dst_applied = self.apply_dst_adjustment(birth_dt)
            result["dst_applied"] = dst_applied
            result["adjusted_time"] = adjusted
            if dst_applied:
                result["metadata"]["dst_period"] = True

        # Step 2: Apply LMT offset
        if apply_lmt:
            lmt_offset = self.get_lmt_offset(location, birth_dt)
            result["lmt_offset"] = lmt_offset
            result["adjusted_time"] = result["adjusted_time"] - timedelta(minutes=abs(lmt_offset))

        # Check for historical LMT uncertainty
        if birth_dt < datetime(1908, 4, 1):
            self.warnings.append(
                {
                    "type": TimezoneWarning.HISTORICAL_LMT,
                    "message": "Pre-1908 birth: City LMT may vary ±8 minutes from calculated value",
                }
            )

        result["warnings"] = self.warnings
        return result

    def validate_input_time(self, dt: datetime) -> Tuple[bool, Optional[str]]:
        """
        Validate if input time is valid (not in DST gap).

        Returns:
            (is_valid, error_message)
        """
        is_gap, msg = self.is_dst_gap(dt)
        if is_gap:
            return False, msg
        return True, None


# Convenience function
def get_saju_adjusted_time(
    birth_dt: datetime, location: str = "Seoul", apply_dst: bool = True, apply_lmt: bool = True
) -> Dict:
    """
    Quick function to get saju-adjusted time.

    Example:
        >>> result = get_saju_adjusted_time(
        ...     datetime(1987, 5, 10, 2, 30),
        ...     location='Seoul'
        ... )
        >>> print(result['adjusted_time'])  # Auto-corrected from DST gap
        >>> print(result['warnings'])  # Shows DST gap warning
    """
    handler = KoreanTimezoneHandler()
    return handler.convert_to_saju_time(birth_dt, location, apply_dst, apply_lmt)
