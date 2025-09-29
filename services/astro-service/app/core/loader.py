from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
import csv

from ..models import TermEntry


@dataclass(slots=True)
class SolarTermLoader:
    """Loader abstraction around the precomputed solar term dataset."""

    table_path: Path

    def load_year(self, year: int) -> Iterable[TermEntry]:
        """Yield solar term entries for the given year from a CSV file."""
        file_path = self.table_path / f"terms_{year}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Solar term table missing for {year}: {file_path}")

        with file_path.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                utc_time = datetime.fromisoformat(row["utc_time"].replace("Z", "+00:00"))
                yield TermEntry(
                    term=row["term"],
                    lambda_deg=float(row["lambda_deg"]),
                    utc_time=utc_time,
                    local_time=utc_time,  # placeholder, conversion handled in service
                    delta_t_seconds=float(row["delta_t_seconds"]),
                    source=row["source"],
                    algo_version=row["algo_version"],
                )
