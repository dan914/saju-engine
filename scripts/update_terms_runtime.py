"""Populate data/terms_<year>.csv from canonical observed and predicted tables."""

from __future__ import annotations

import shutil
from pathlib import Path

OBSERVED_DIR = Path('data/canonical/terms')
PREDICTED_DIR = Path('data/canonical/terms_predicted')
RUNTIME_DIR = Path('data')
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

OBSERVED_RANGE = range(1930, 2021)
PREDICTED_RANGE = range(2021, 2051)


def copy_year(src_dir: Path, year: int) -> None:
    src = src_dir / f'terms_{year}.csv'
    if not src.exists():
        raise FileNotFoundError(f'Missing terms file for {year}: {src}')
    dst = RUNTIME_DIR / f'terms_{year}.csv'
    shutil.copy2(src, dst)
    print(f'Updated {dst}')


def main() -> None:
    for year in OBSERVED_RANGE:
        copy_year(OBSERVED_DIR, year)
    for year in PREDICTED_RANGE:
        copy_year(PREDICTED_DIR, year)


if __name__ == '__main__':
    main()
