"""Generate solar term tables using Meeus-style solar longitude calculations."""

from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

TERMS = [
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

TERM_LONGITUDE: Dict[str, float] = {
    "小寒": 285.0,
    "大寒": 300.0,
    "立春": 315.0,
    "雨水": 330.0,
    "驚蟄": 345.0,
    "春分": 0.0,
    "清明": 15.0,
    "穀雨": 30.0,
    "立夏": 45.0,
    "小滿": 60.0,
    "芒種": 75.0,
    "夏至": 90.0,
    "小暑": 105.0,
    "大暑": 120.0,
    "立秋": 135.0,
    "處暑": 150.0,
    "白露": 165.0,
    "秋分": 180.0,
    "寒露": 195.0,
    "霜降": 210.0,
    "立冬": 225.0,
    "小雪": 240.0,
    "大雪": 255.0,
    "冬至": 270.0,
}

# Approximate calendar dates (month, day) in UTC for initial estimates
TERM_APPROX: Dict[str, tuple[int, int]] = {
    "小寒": (1, 5),
    "大寒": (1, 20),
    "立春": (2, 4),
    "雨水": (2, 19),
    "驚蟄": (3, 6),
    "春分": (3, 21),
    "清明": (4, 5),
    "穀雨": (4, 20),
    "立夏": (5, 5),
    "小滿": (5, 21),
    "芒種": (6, 6),
    "夏至": (6, 21),
    "小暑": (7, 7),
    "大暑": (7, 23),
    "立秋": (8, 7),
    "處暑": (8, 23),
    "白露": (9, 7),
    "秋分": (9, 23),
    "寒露": (10, 8),
    "霜降": (10, 24),
    "立冬": (11, 7),
    "小雪": (11, 22),
    "大雪": (12, 7),
    "冬至": (12, 21),
}

OUTPUT_ROOT = Path("data/canonical/terms_astronomy")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi


def datetime_to_jd(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    year = dt.year
    month = dt.month
    day = (
        dt.day + dt.hour / 24 + dt.minute / 1440 + dt.second / 86400 + dt.microsecond / 86400 / 1e6
    )
    if month <= 2:
        year -= 1
        month += 12
    A = year // 100
    B = 2 - A + A // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    return jd


def jd_to_datetime(jd: float) -> datetime:
    Z = int(jd + 0.5)
    F = jd + 0.5 - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - alpha // 4
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715
    day_floor = int(day)
    frac = day - day_floor
    hours = frac * 24
    hour = int(hours)
    minutes = (hours - hour) * 60
    minute = int(minutes)
    seconds = (minutes - minute) * 60
    second = int(seconds)
    micro = int(round((seconds - second) * 1_000_000))
    return datetime(year, month, day_floor, hour, minute, second, micro, tzinfo=timezone.utc)


def delta_t_seconds(year: float) -> float:
    # Rough polynomial approximations (NASA) sufficient to within a few seconds.
    if 1900 <= year < 1980:
        t = year - 1900
        return -0.00002 * t**3 + 0.00631686 * t**2 + 0.775518 * t + 32.0
    if 1980 <= year <= 2100:
        t = year - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t**2
    # Fallback linear extrapolation beyond 2100
    return 62.92 + 0.32217 * (year - 2000)


def solar_longitude(jd_ut: float) -> float:
    # Convert to terrestrial time using ΔT estimate
    year = jd_to_datetime(jd_ut).year
    jd_tt = jd_ut + delta_t_seconds(year) / 86400.0
    T = (jd_tt - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    M += 0.00000048 * T * T * T
    M_rad = math.radians(M)
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T * T
    C = (
        (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_rad)
        + (0.019993 - 0.000101 * T) * math.sin(2 * M_rad)
        + 0.000289 * math.sin(3 * M_rad)
    )
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    lambda_sun = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    return lambda_sun % 360


def normalise_angle(angle: float) -> float:
    return angle % 360


def find_term_time(year: int, term: str) -> datetime:
    target = TERM_LONGITUDE[term]
    month, day = TERM_APPROX[term]
    guess = datetime(year, month, day, 12, tzinfo=timezone.utc)
    jd = datetime_to_jd(guess)
    for _ in range(20):
        lon = solar_longitude(jd)
        diff = (lon - target + 180) % 360 - 180
        if abs(diff) < 5e-6:
            break
        delta = 0.0001
        lon2 = solar_longitude(jd + delta)
        derivative = (lon2 - lon) / delta
        if abs(derivative) < 1e-12:
            derivative = 1e-12
        jd -= diff / derivative
    return jd_to_datetime(jd)


def generate_year(year: int) -> list[dict[str, str]]:
    rows = []
    for term in TERMS:
        dt_utc = find_term_time(year, term)
        rows.append(
            {
                "term": term,
                "lambda_deg": str(TERM_LONGITUDE[term]),
                "utc_time": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "delta_t_seconds": "0.0",
                "source": "ASTRONOMY_SOLVER",
                "algo_version": "Meeus-approx",
            }
        )
    rows.sort(key=lambda r: r["utc_time"])
    return rows


def write_year(year: int, rows: list[dict[str, str]]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_ROOT / f"terms_{year}.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
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
        writer.writerows(rows)
    print(f"Generated terms for {year} → {path}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=int, help="Start year (inclusive)")
    parser.add_argument("end", type=int, help="End year (inclusive)")
    args = parser.parse_args()
    for year in range(args.start, args.end + 1):
        rows = generate_year(year)
        write_year(year, rows)


if __name__ == "__main__":
    main()
