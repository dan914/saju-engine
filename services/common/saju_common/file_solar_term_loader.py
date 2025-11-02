"""
File-based solar term loader for CSV data.

Loads precomputed solar term data from CSV files in the /data/ directory.
This is the same refined astronomical data used by the pillars calculation engine.

Source: SAJU_LITE_REFINED (v1.5.10+astro)
Coverage: 1900-2050+
Precision: Includes ΔT corrections for historical accuracy

Usage:
    >>> from saju_common import FileSolarTermLoader
    >>> loader = FileSolarTermLoader(Path("/path/to/data"))
    >>> entries = list(loader.load_year(2000))
    >>> print(entries[0].term, entries[0].utc_time)
    小寒 2000-01-06 00:56:26+00:00

Version: 1.0.0
Date: 2025-10-10
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class SolarTermEntry:
    """
    Simplified solar term entry for luck calculation.

    Attributes:
        term: Chinese name of solar term (e.g., "立春", "小寒")
        utc_time: Exact UTC datetime of solar term occurrence
    """

    term: str
    utc_time: datetime


@dataclass(slots=True)
class FileSolarTermLoader:
    """
    Loads solar terms from CSV files in data/ directory.

    CSV Format:
        term,lambda_deg,utc_time,delta_t_seconds,source,algo_version
        小寒,0,2000-01-06T00:56:26Z,62.93,SAJU_LITE_REFINED,v1.5.10+astro

    Attributes:
        table_path: Path to directory containing terms_YYYY.csv files
    """

    table_path: Path

    def load_year(self, year: int) -> Iterable[SolarTermEntry]:
        """
        Yield solar term entries for the given year.

        Args:
            year: Year to load (e.g., 2000)

        Returns:
            Iterable of SolarTermEntry objects (24 per year)

        Raises:
            FileNotFoundError: If CSV file for year doesn't exist

        Example:
            >>> loader = FileSolarTermLoader(Path("data"))
            >>> terms = list(loader.load_year(2000))
            >>> len(terms)
            24
        """
        file_path = self.table_path / f"terms_{year}.csv"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Solar term data missing for year {year}. " f"Expected file: {file_path}"
            )

        with file_path.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Parse ISO 8601 UTC timestamp
                utc_time = datetime.fromisoformat(row["utc_time"].replace("Z", "+00:00"))
                yield SolarTermEntry(term=row["term"], utc_time=utc_time)
