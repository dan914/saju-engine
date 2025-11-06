"""Utility for loading SKY_LIZARD canonical year/month mappings."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Optional

CANONICAL_DIR = Path(__file__).resolve().parents[4] / "data" / "canonical"
PILLAR_FILES = [
    "pillars_canonical_1930_1959.csv",
    "pillars_canonical_1960_1989.csv",
    "pillars_canonical_1990_2009.csv",
    "pillars_canonical_2010_2029.csv",
    "pillars_generated_2021_2050.csv",
]


class CanonicalCalendar:
    """Loads canonical pillar data into memory on demand."""

    def __init__(self) -> None:
        self._loaded = False
        self._year_map: Dict[str, str] = {}
        self._month_map: Dict[str, str] = {}

    def _load(self) -> None:
        if self._loaded:
            return
        for filename in PILLAR_FILES:
            path = CANONICAL_DIR / filename
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    date_key = row.get("local_datetime", "")[:10]
                    if not date_key:
                        continue
                    year_pillar = (row.get("year_pillar") or "").strip()
                    month_pillar = (row.get("month_pillar") or "").strip()
                    if year_pillar:
                        self._year_map[date_key] = year_pillar
                    if month_pillar:
                        self._month_map[date_key] = month_pillar
        self._loaded = True

    def year_pillar(self, date_key: str) -> Optional[str]:
        self._load()
        return self._year_map.get(date_key)

    def month_pillar(self, date_key: str) -> Optional[str]:
        self._load()
        return self._month_map.get(date_key)


canonical_calendar = CanonicalCalendar()
