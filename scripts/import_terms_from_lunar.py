"""Generate solar term CSVs (terms_<year>.csv) from SKY_LIZARD canonical dataset."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANSE_MASTER = REPO_ROOT / "data" / "canonical" / "manse_master.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "canonical" / "terms"

KOREAN_TO_TERM = {
    "입춘": "立春",
    "우수": "雨水",
    "경칩": "驚蟄",
    "춘분": "春分",
    "청명": "清明",
    "곡우": "穀雨",
    "입하": "立夏",
    "소만": "小滿",
    "망종": "芒種",
    "하지": "夏至",
    "소서": "小暑",
    "대서": "大暑",
    "입추": "立秋",
    "처서": "處暑",
    "백로": "白露",
    "추분": "秋分",
    "한로": "寒露",
    "상강": "霜降",
    "입동": "立冬",
    "소설": "小雪",
    "대설": "大雪",
    "동지": "冬至",
    "소한": "小寒",
    "대한": "大寒",
}

MONTH_24_TO_TERM = {
    0: "大雪",
    1: "小寒",
    2: "立春",
    3: "驚蟄",
    4: "清明",
    5: "立夏",
    6: "芒種",
    7: "小暑",
    8: "立秋",
    9: "白露",
    10: "寒露",
    11: "立冬",
}

TERM_ORDER = [
    "小寒",
    "大寒",
    "立春",
    "雨水",
    "驚蟄",
    "春分",
    "清明",
    "穀雨",
    "立夏",
    "小滿",
    "芒種",
    "夏至",
    "小暑",
    "大暑",
    "立秋",
    "處暑",
    "白露",
    "秋分",
    "寒露",
    "霜降",
    "立冬",
    "小雪",
    "大雪",
    "冬至",
]

TERM_TO_LAMBDA = {term: (idx * 15) % 360 for idx, term in enumerate(TERM_ORDER)}

KST_OFFSET = timedelta(hours=9)


def parse_rows() -> dict[int, list[dict[str, str]]]:
    year_terms: dict[int, list[dict[str, str]]] = defaultdict(list)
    with MANSE_MASTER.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        previous_month_24: str | None = None
        for row in reader:
            solar_date = row.get("solar_date", "").strip()
            if not solar_date:
                continue
            month_24 = row.get("month_24", "").strip()
            if not month_24:
                previous_month_24 = month_24 or previous_month_24
                continue
            if previous_month_24 is None:
                previous_month_24 = month_24
                continue
            if month_24 == previous_month_24:
                continue
            term = KOREAN_TO_TERM.get(row.get("jeol", ""))
            # Some exports do not store the Korean term; derive from month_24 instead.
            if not term:
                try:
                    term = MONTH_24_TO_TERM[int(month_24)]
                except (ValueError, KeyError):
                    term = None
            if not term:
                previous_month_24 = month_24
                continue

            try:
                year = int(solar_date.split("-")[0])
            except ValueError:
                previous_month_24 = month_24
                continue
            if year < 1930 or year > 2020:
                previous_month_24 = month_24
                continue

            try:
                base_dt = datetime.strptime(solar_date, "%Y-%m-%d")
            except ValueError:
                previous_month_24 = month_24
                continue

            div_hour = row.get("div_hour", "").strip()
            div_minute = row.get("div_minute", "").strip()
            hour = int(div_hour) if div_hour.isdigit() else 0
            minute = int(div_minute) if div_minute.isdigit() else 0
            local_dt = base_dt.replace(hour=hour, minute=minute)
            utc_dt = (local_dt - KST_OFFSET).replace(tzinfo=timezone.utc)

            entry = {
                "term": term,
                "utc_time": utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lambda_deg": f"{TERM_TO_LAMBDA.get(term, 0)}",
                "delta_t_seconds": "0.0",
                "source": "SKY_LIZARD_CANONICAL",
                "algo_version": "SL-DB-v10.4",
            }
            year_terms[year].append(entry)
            previous_month_24 = month_24
    return year_terms


def write_year_files(year_terms: dict[int, list[dict[str, str]]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for year, entries in sorted(year_terms.items()):
        entries.sort(key=lambda item: (TERM_ORDER.index(item["term"]), item["utc_time"]))
        out_path = OUTPUT_DIR / f"terms_{year}.csv"
        if len(entries) != 12:
            print(f"Skipping year {year}: only {len(entries)} term boundaries detected")
            continue
        with out_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "term",
                    "lambda_deg",
                    "utc_time",
                    "delta_t_seconds",
                    "source",
                    "algo_version",
                ],
            )
            writer.writeheader()
            writer.writerows(entries)
        print(f"Wrote terms for {year}")


def main() -> None:
    if not MANSE_MASTER.exists():
        raise SystemExit("Canonical manse_master.csv not found. Run canonical import first.")
    year_terms = parse_rows()
    write_year_files(year_terms)


if __name__ == "__main__":
    main()
