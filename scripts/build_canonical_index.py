"""Generate summary metadata for the SKY_LIZARD canonical dataset."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

CANONICAL_ROOT = Path(__file__).resolve().parents[1] / "data" / "canonical"


@dataclass
class FileStats:
    filename: str
    record_count: int = 0
    tz_set: set[str] = field(default_factory=set)
    start_dt: datetime | None = None
    end_dt: datetime | None = None

    def update(self, row: dict[str, str]) -> None:
        self.record_count += 1
        tz = row.get("timezone")
        if tz:
            self.tz_set.add(tz)
        raw_dt = row.get("local_datetime")
        if raw_dt:
            try:
                dt = datetime.fromisoformat(raw_dt)
            except ValueError:
                return
            if self.start_dt is None or dt < self.start_dt:
                self.start_dt = dt
            if self.end_dt is None or dt > self.end_dt:
                self.end_dt = dt

    def serialise(self) -> dict[str, object]:
        return {
            "filename": self.filename,
            "records": self.record_count,
            "timezones": sorted(self.tz_set),
            "start": self.start_dt.isoformat() if self.start_dt else None,
            "end": self.end_dt.isoformat() if self.end_dt else None,
        }


def iter_canonical_csv(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    yield from sorted(root.glob("*.csv"))


def build_index(root: Path) -> dict[str, object]:
    manifest: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "files": [],
        "total_records": 0,
        "timezones": [],
    }
    tz_union: set[str] = set()
    total = 0
    for csv_path in iter_canonical_csv(root):
        stats = FileStats(filename=csv_path.name)
        with csv_path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                stats.update(row)
        manifest["files"].append(stats.serialise())
        tz_union.update(stats.tz_set)
        total += stats.record_count
    manifest["total_records"] = total
    manifest["timezones"] = sorted(tz_union)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=CANONICAL_ROOT,
        help="Canonical dataset directory (default: data/canonical)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Path to write JSON summary (default: <root>/index.json)",
    )
    args = parser.parse_args()
    root = args.root
    manifest = build_index(root)
    out_path = args.out or (root / "index.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote canonical index → {out_path}")


if __name__ == "__main__":
    main()
