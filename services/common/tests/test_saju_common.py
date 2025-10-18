"""
Tests for Saju Common Package

Tests verify:
1. BasicTimeResolver: TZ roundtrip conversions
2. TableSolarTermLoader: Month → Branch → Season mapping
3. SimpleDeltaT: ΔT calculation for modern dates
4. Protocol compliance
"""

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from saju_common import (
    BRANCH_TO_SEASON,
    SEASON_ELEMENT_BOOST,
    BasicTimeResolver,
    DeltaTPolicy,
    SimpleDeltaT,
    SolarTermLoader,
    TableSolarTermLoader,
    TimeResolver,
)


class TestBasicTimeResolver:
    """Test BasicTimeResolver implementation"""

    def test_protocol_compliance(self):
        """Verify BasicTimeResolver implements TimeResolver protocol"""
        resolver = BasicTimeResolver()
        assert isinstance(resolver, TimeResolver)

    def test_to_utc_seoul(self):
        """Test Seoul local time → UTC conversion"""
        resolver = BasicTimeResolver()
        local_dt = datetime(2025, 1, 15, 10, 30, 0)  # Naive
        utc_dt = resolver.to_utc(local_dt, "Asia/Seoul")

        # Seoul is UTC+9
        assert utc_dt.hour == 1
        assert utc_dt.minute == 30
        assert utc_dt.tzinfo == ZoneInfo("UTC")

    def test_from_utc_seoul(self):
        """Test UTC → Seoul local time conversion"""
        resolver = BasicTimeResolver()
        utc_dt = datetime(2025, 1, 15, 1, 30, 0, tzinfo=timezone.utc)
        local_dt = resolver.from_utc(utc_dt, "Asia/Seoul")

        # Seoul is UTC+9
        assert local_dt.hour == 10
        assert local_dt.minute == 30
        assert local_dt.tzinfo == ZoneInfo("Asia/Seoul")

    def test_roundtrip(self):
        """Test UTC → Local → UTC roundtrip"""
        resolver = BasicTimeResolver()
        original_utc = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # UTC → Seoul → UTC
        local = resolver.from_utc(original_utc, "Asia/Seoul")
        back_to_utc = resolver.to_utc(local, "Asia/Seoul")

        assert back_to_utc == original_utc

    def test_dst_transition(self):
        """Test DST handling (using US/Pacific)"""
        resolver = BasicTimeResolver()

        # Standard time (PST: UTC-8)
        winter_local = datetime(2025, 1, 15, 10, 0, 0)
        winter_utc = resolver.to_utc(winter_local, "US/Pacific")
        assert winter_utc.hour == 18  # 10 + 8

        # Daylight time (PDT: UTC-7)
        summer_local = datetime(2025, 7, 15, 10, 0, 0)
        summer_utc = resolver.to_utc(summer_local, "US/Pacific")
        assert summer_utc.hour == 17  # 10 + 7


class TestTableSolarTermLoader:
    """Test TableSolarTermLoader implementation"""

    def test_protocol_compliance(self):
        """Verify TableSolarTermLoader implements SolarTermLoader protocol"""
        loader = TableSolarTermLoader()
        assert isinstance(loader, SolarTermLoader)

    def test_month_branch_february(self):
        """Test February → 寅 (spring month)"""
        loader = TableSolarTermLoader()
        d = date(2025, 2, 15)
        branch = loader.month_branch(d)
        assert branch == "寅"

    def test_month_branch_december(self):
        """Test December → 子 (winter month)"""
        loader = TableSolarTermLoader()
        d = date(2025, 12, 15)
        branch = loader.month_branch(d)
        assert branch == "子"

    def test_season_spring(self):
        """Test spring season (寅卯)"""
        loader = TableSolarTermLoader()
        assert loader.season(date(2025, 2, 15)) == "spring"  # 寅
        assert loader.season(date(2025, 3, 15)) == "spring"  # 卯

    def test_season_summer(self):
        """Test summer season (巳午)"""
        loader = TableSolarTermLoader()
        assert loader.season(date(2025, 5, 15)) == "summer"  # 巳
        assert loader.season(date(2025, 6, 15)) == "summer"  # 午

    def test_season_long_summer(self):
        """Test long_summer (土旺 season: 辰未戌丑)"""
        loader = TableSolarTermLoader()
        assert loader.season(date(2025, 1, 15)) == "long_summer"  # 丑
        assert loader.season(date(2025, 4, 15)) == "long_summer"  # 辰
        assert loader.season(date(2025, 7, 15)) == "long_summer"  # 未
        assert loader.season(date(2025, 10, 15)) == "long_summer"  # 戌

    def test_season_autumn(self):
        """Test autumn season (申酉)"""
        loader = TableSolarTermLoader()
        assert loader.season(date(2025, 8, 15)) == "autumn"  # 申
        assert loader.season(date(2025, 9, 15)) == "autumn"  # 酉

    def test_season_winter(self):
        """Test winter season (亥子)"""
        loader = TableSolarTermLoader()
        assert loader.season(date(2025, 11, 15)) == "winter"  # 亥
        assert loader.season(date(2025, 12, 15)) == "winter"  # 子


class TestSimpleDeltaT:
    """Test SimpleDeltaT implementation"""

    def test_protocol_compliance(self):
        """Verify SimpleDeltaT implements DeltaTPolicy protocol"""
        dt = SimpleDeltaT()
        assert isinstance(dt, DeltaTPolicy)

    def test_year_2000_baseline(self):
        """Test ΔT at year 2000 (baseline)"""
        dt = SimpleDeltaT()
        result = dt.delta_t_seconds(2000, 1)
        assert result == 69.0

    def test_year_2025_linear(self):
        """Test ΔT at year 2025 (linear increase)"""
        dt = SimpleDeltaT()
        result = dt.delta_t_seconds(2025, 1)
        # 69 + 0.1 * (2025 - 2000) = 69 + 2.5 = 71.5
        assert result == 71.5

    def test_year_1990_clamped(self):
        """Test ΔT before 2000 is clamped to 69.0"""
        dt = SimpleDeltaT()
        result = dt.delta_t_seconds(1990, 1)
        # max(0, 1990 - 2000) = 0, so 69 + 0.1 * 0 = 69
        assert result == 69.0

    def test_month_ignored(self):
        """Test month parameter doesn't affect linear model"""
        dt = SimpleDeltaT()
        jan = dt.delta_t_seconds(2025, 1)
        dec = dt.delta_t_seconds(2025, 12)
        assert jan == dec == 71.5


class TestMappingTables:
    """Test static mapping tables"""

    def test_branch_to_season_coverage(self):
        """Verify all 12 branches have season mapping"""
        branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        for branch in branches:
            assert branch in BRANCH_TO_SEASON
            season = BRANCH_TO_SEASON[branch]
            assert season in ["spring", "summer", "long_summer", "autumn", "winter"]

    def test_season_element_boost_structure(self):
        """Verify season boost has all 5 seasons"""
        assert "spring" in SEASON_ELEMENT_BOOST
        assert "summer" in SEASON_ELEMENT_BOOST
        assert "long_summer" in SEASON_ELEMENT_BOOST
        assert "autumn" in SEASON_ELEMENT_BOOST
        assert "winter" in SEASON_ELEMENT_BOOST

    def test_season_element_boost_values(self):
        """Verify boost values are reasonable (-10 to +10)"""
        for season, boosts in SEASON_ELEMENT_BOOST.items():
            for element, boost in boosts.items():
                assert -10 <= boost <= 10, f"{season}.{element} boost {boost} out of range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
