"""Generate solar term tables (apparent Sun λ) using Meeus-style algorithm."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable
from zoneinfo import ZoneInfo

DEG = math.pi / 180.0
TWO_PI = 2 * math.pi

TERMS_SEQUENCE = [
    "小寒",
    "立春",
    "驚蟄",
    "清明",
    "立夏",
    "芒種",
    "小暑",
    "立秋",
    "白露",
    "寒露",
    "立冬",
    "大雪",
]

TERMS_LONGITUDE: Dict[str, float] = {
    "小寒": 0.0,
    "立春": 30.0,
    "驚蟄": 60.0,
    "清明": 90.0,
    "立夏": 120.0,
    "芒種": 150.0,
    "小暑": 180.0,
    "立秋": 210.0,
    "白露": 240.0,
    "寒露": 270.0,
    "立冬": 300.0,
    "大雪": 330.0,
}

# Approximate calendar seeds (month, day) in UTC for initial brackets
TERM_APPROX = {
    "小寒": (1, 5),
    "立春": (2, 4),
    "驚蟄": (3, 6),
    "清明": (4, 5),
    "立夏": (5, 6),
    "芒種": (6, 6),
    "小暑": (7, 7),
    "立秋": (8, 8),
    "白露": (9, 7),
    "寒露": (10, 8),
    "立冬": (11, 7),
    "大雪": (12, 7),
}

OUTPUT_DIR = Path("data/canonical/terms_ephem")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TermResult:
    name: str
    longitude_deg: float
    jd_tt: float
    dt_utc: datetime
    dt_kst: datetime
    dt_myt: datetime
    delta_t_sec: float


def datetime_to_jd(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)
    year = dt_utc.year
    month = dt_utc.month
    day = (
        dt_utc.day
        + (
            dt_utc.hour
            + (dt_utc.minute + (dt_utc.second + dt_utc.microsecond / 1_000_000) / 60.0) / 60.0
        )
        / 24.0
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
    frac_day = day - day_floor
    hours = frac_day * 24
    hour = int(hours)
    minutes = (hours - hour) * 60
    minute = int(minutes)
    seconds = (minutes - minute) * 60
    second = int(seconds)
    microsecond = int(round((seconds - second) * 1_000_000))
    return datetime(year, month, day_floor, hour, minute, second, microsecond, tzinfo=timezone.utc)


def delta_t_seconds(year: int, month: int) -> float:
    y = year + (month - 0.5) / 12.0
    if 1900 <= y < 1999:
        t = y - 1900
        return -0.00002 * t**3 + 0.00631686 * t**2 + 0.775518 * t + 32.0
    if 1999 <= y <= 2150:
        t = y - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t * t
    # fallback linear extrapolation
    t = y - 2000
    return 62.92 + 0.32217 * t


def sun_lambda_apparent_tt(jd_tt: float) -> float:
    T = (jd_tt - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T - 0.00000048 * T * T * T
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T * T
    M_rad = math.radians(M)
    C = (
        (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_rad)
        + (0.019993 - 0.000101 * T) * math.sin(2 * M_rad)
        + 0.000289 * math.sin(3 * M_rad)
    )
    true_long = L0 + C
    omega = math.radians(125.04 - 1934.136 * T)
    lambda_apparent = true_long - 0.00569 - 0.00478 * math.sin(omega)
    return math.radians(lambda_apparent % 360)


def wrap_angle(angle: float) -> float:
    wrapped = angle % TWO_PI
    if wrapped > math.pi:
        wrapped -= TWO_PI
    return wrapped


def bracket_term(seed_tt: float, lam_target: float) -> tuple[float, float]:
    step = 0.25  # days (~6h)
    span_days = 12
    lower = seed_tt - span_days / 2
    upper = lower + step
    f_lower = wrap_angle(sun_lambda_apparent_tt(lower) - lam_target)
    for _ in range(int(span_days / step) + 8):
        f_upper = wrap_angle(sun_lambda_apparent_tt(upper) - lam_target)
        if f_lower * f_upper <= 0:
            return lower, upper
        lower, f_lower = upper, f_upper
        upper += step
    raise RuntimeError("Failed to bracket solar term root")


def find_crossing(jd_tt_seed: float, lam_target: float) -> float:
    lower, upper = bracket_term(jd_tt_seed, lam_target)
    f_lower = wrap_angle(sun_lambda_apparent_tt(lower) - lam_target)
    f_upper = wrap_angle(sun_lambda_apparent_tt(upper) - lam_target)
    for _ in range(64):
        mid = 0.5 * (lower + upper)
        f_mid = wrap_angle(sun_lambda_apparent_tt(mid) - lam_target)
        if abs((upper - lower) * 86400) < 0.5:
            return mid
        if f_lower * f_mid <= 0:
            upper, f_upper = mid, f_mid
        else:
            lower, f_lower = mid, f_mid
    return 0.5 * (lower + upper)


def term_results_for_year(year: int, prev_term_tt: Dict[str, float]) -> Iterable[TermResult]:
    terms_sorted = sorted(TERMS_LONGITUDE.items(), key=lambda item: item[1])
    for term_name, longitude_deg in terms_sorted:
        month_seed, day_seed = TERM_APPROX[term_name]
        if term_name in prev_term_tt:
            seed_tt = prev_term_tt[term_name] + 365.2422
        else:
            month_seed, day_seed = TERM_APPROX[term_name]
            approx_dt = datetime(
                year if month_seed > 1 else year, month_seed, day_seed, 12, tzinfo=timezone.utc
            )
            delta_t = delta_t_seconds(year, month_seed)
            seed_tt = datetime_to_jd(approx_dt) + delta_t / 86400.0

        lam_target_rad = math.radians(longitude_deg)
        try:
            tt_cross = find_crossing(seed_tt, lam_target_rad)
        except RuntimeError:
            approx_dt = datetime(year, month_seed, day_seed, 12, tzinfo=timezone.utc)
            alt_seed = datetime_to_jd(approx_dt) + delta_t_seconds(year, month_seed) / 86400.0
            tt_cross = find_crossing(alt_seed, lam_target_rad)
        delta_t = delta_t_seconds(year, month_seed)
        jd_utc = tt_cross - delta_t / 86400.0
        dt_utc = jd_to_datetime(jd_utc)
        kst = dt_utc.astimezone(ZoneInfo("Asia/Seoul"))
        myt = dt_utc.astimezone(ZoneInfo("Asia/Kuching"))
        prev_term_tt[term_name] = tt_cross
        yield TermResult(term_name, longitude_deg, tt_cross, dt_utc, kst, myt, delta_t)


def write_year(year: int, results: Iterable[TermResult]) -> None:
    rows = sorted(results, key=lambda r: TERMS_LONGITUDE[r.name])
    path = OUTPUT_DIR / f"terms_{year}.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "term",
                "term_deg",
                "utc",
                "kst",
                "myt",
                "delta_t_seconds",
                "source",
                "algo_version",
            ],
        )
        writer.writeheader()
        for result in rows:
            writer.writerow(
                {
                    "term": result.name,
                    "term_deg": f"{result.longitude_deg:.1f}",
                    "utc": result.dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                    "kst": result.dt_kst.isoformat(),
                    "myt": result.dt_myt.isoformat(),
                    "delta_t_seconds": f"{result.delta_t_sec:.2f}",
                    "source": "meeus_apparent",
                    "algo_version": "v1",
                }
            )


def main(start: int, end: int) -> None:
    prev_term_tt: Dict[str, float] = {}
    for year in range(start, end + 1):
        results = list(term_results_for_year(year, prev_term_tt))
        write_year(year, results)
        print(f"Generated terms for {year}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    args = parser.parse_args()
    from zoneinfo import ZoneInfo  # ensure available

    main(args.start, args.end)
