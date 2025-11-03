"""Normalize SKY_LIZARD manse exports into canonical pillar CSVs."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]

# Use Poetry-based imports via script loader
from scripts._script_loader import get_pillars_module

# Load required classes/functions from services
month_pillar = get_pillars_module("pillars", "month_pillar")

CANONICAL_DIR = REPO_ROOT / "data" / "canonical"
MANSE_MASTER = CANONICAL_DIR / "manse_master.csv"

TARGET_FILES = {
    "pillars_canonical_1930_1959.csv": ("1930-01-01", "1959-12-31"),
    "pillars_canonical_1960_1989.csv": ("1960-01-01", "1989-12-31"),
    "pillars_canonical_1990_2009.csv": ("1990-01-01", "2009-12-31"),
    "pillars_canonical_2010_2029.csv": ("2010-01-01", "2029-12-31"),
}

SEXAGENARY = [
    "甲子",
    "乙丑",
    "丙寅",
    "丁卯",
    "戊辰",
    "己巳",
    "庚午",
    "辛未",
    "壬申",
    "癸酉",
    "甲戌",
    "乙亥",
    "丙子",
    "丁丑",
    "戊寅",
    "己卯",
    "庚辰",
    "辛巳",
    "壬午",
    "癸未",
    "甲申",
    "乙酉",
    "丙戌",
    "丁亥",
    "戊子",
    "己丑",
    "庚寅",
    "辛卯",
    "壬辰",
    "癸巳",
    "甲午",
    "乙未",
    "丙申",
    "丁酉",
    "戊戌",
    "己亥",
    "庚子",
    "辛丑",
    "壬寅",
    "癸卯",
    "甲辰",
    "乙巳",
    "丙午",
    "丁未",
    "戊申",
    "己酉",
    "庚戌",
    "辛亥",
    "壬子",
    "癸丑",
    "甲寅",
    "乙卯",
    "丙辰",
    "丁巳",
    "戊午",
    "己未",
    "庚申",
    "辛酉",
    "壬戌",
    "癸亥",
]

STEM_MAP = {
    "갑": "甲",
    "을": "乙",
    "병": "丙",
    "정": "丁",
    "무": "戊",
    "기": "己",
    "경": "庚",
    "신": "辛",
    "임": "壬",
    "계": "癸",
}

BRANCH_MAP = {
    "자": "子",
    "축": "丑",
    "인": "寅",
    "묘": "卯",
    "진": "辰",
    "사": "巳",
    "오": "午",
    "미": "未",
    "신": "申",
    "유": "酉",
    "술": "戌",
    "해": "亥",
}

MONTH_24_TO_BRANCH = {
    0: "子",  # 大雪
    1: "丑",  # 小寒
    2: "寅",  # 立春
    3: "卯",  # 驚蟄
    4: "辰",  # 清明
    5: "巳",  # 立夏
    6: "午",  # 芒種
    7: "未",  # 小暑
    8: "申",  # 立秋
    9: "酉",  # 白露
    10: "戌",  # 寒露
    11: "亥",  # 立冬
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

DEFAULT_TIME = "T12:00:00"
DEFAULT_TZ = "Asia/Seoul"
DEFAULT_LAT = "37.5665"
DEFAULT_LON = "126.9784"
DATASET_VERSION = "SL-DB-v10.4"


def hangul_to_sexagenary(label: str) -> str:
    label = label.strip()
    if not label:
        return ""
    if len(label) < 2:
        raise ValueError(f"Unexpected ganji label: {label!r}")
    stem_char = STEM_MAP.get(label[0])
    branch_char = BRANCH_MAP.get(label[1])
    if not stem_char or not branch_char:
        raise ValueError(f"Unable to map ganji label: {label!r}")
    return stem_char + branch_char


def index_to_sexagenary(index: str) -> str:
    if not index:
        return ""
    try:
        idx = int(index)
    except ValueError:
        return ""
    return SEXAGENARY[idx % 60]


def build_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    with MANSE_MASTER.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            solar_date = row["solar_date"].strip()
            if not solar_date:
                continue
            year_pillar = index_to_sexagenary(row.get("yunju", ""))
            month_term = MONTH_24_TO_TERM.get(int(row["month_24"])) if row["month_24"] else ""
            month_branch = MONTH_24_TO_BRANCH.get(int(row["month_24"])) if row["month_24"] else ""
            month_pillar_value = ""
            if year_pillar and month_branch:
                month_pillar_value = month_pillar(year_pillar[0], month_branch)
            day_pillar = hangul_to_sexagenary(row.get("ganji", ""))
            record = {
                "solar_date": solar_date,
                "local_datetime": f"{solar_date}{DEFAULT_TIME}",
                "timezone": DEFAULT_TZ,
                "longitude_deg": DEFAULT_LON,
                "latitude_deg": DEFAULT_LAT,
                "year_pillar": year_pillar,
                "month_pillar": month_pillar_value,
                "day_pillar": day_pillar,
                "hour_pillar": "",  # Hour information not provided in source dataset
                "month_term": month_term or "",
                "delta_t_seconds": "",
                "dataset_version": DATASET_VERSION,
                "notes": json.dumps(
                    {
                        "num": row.get("num"),
                        "solar_yun": row.get("solar_yun"),
                        "lunar_date": row.get("lunar_date"),
                        "lunar_yun": row.get("lunar_yun"),
                        "month_code": row.get("month_code"),
                        "month_24": row.get("month_24"),
                        "day_time": row.get("day_time"),
                        "div_hour": row.get("div_hour"),
                        "div_minute": row.get("div_minute"),
                    },
                    ensure_ascii=False,
                ),
            }
            records.append(record)
    return records


def write_partitions(records: Iterable[dict[str, str]]) -> None:
    partitions = {name: [] for name in TARGET_FILES}
    for record in records:
        solar_date = record["solar_date"]
        for filename, (start, end) in TARGET_FILES.items():
            if start <= solar_date <= end:
                partitions[filename].append(record)
                break
    for filename, rows in partitions.items():
        out_path = CANONICAL_DIR / filename
        with out_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "local_datetime",
                    "timezone",
                    "longitude_deg",
                    "latitude_deg",
                    "year_pillar",
                    "month_pillar",
                    "day_pillar",
                    "hour_pillar",
                    "month_term",
                    "delta_t_seconds",
                    "dataset_version",
                    "notes",
                ],
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row[key] for key in writer.fieldnames})
        print(f"Wrote {len(rows)} rows → {filename}")


def main() -> None:
    if not MANSE_MASTER.exists():
        raise SystemExit("Expected manse_master.csv in data/canonical")
    records = build_records()
    write_partitions(records)


if __name__ == "__main__":
    main()
