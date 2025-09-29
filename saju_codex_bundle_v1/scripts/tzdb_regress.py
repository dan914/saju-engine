#!/usr/bin/env python3
import argparse
import csv
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def parse_args():
    ap = argparse.ArgumentParser(description="Compare local→UTC offsets between two tzdb paths")
    ap.add_argument("--old-tzpath", required=True, help="Directory containing old zoneinfo files")
    ap.add_argument("--new-tzpath", required=True, help="Directory containing new zoneinfo files")
    ap.add_argument("--samples", required=True, help="CSV with columns: zone,local_datetime,note")
    ap.add_argument("--threshold", type=float, default=1.0, help="Seconds threshold to flag")
    ap.add_argument("--out-json", default="tzdb_report.json")
    ap.add_argument("--out-csv", default="tzdb_report.csv")
    return ap.parse_args()


def load_samples(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def _aware_from_wall(dt_str, zone, tzpath, fold=None):
    # Expect format "YYYY-MM-DD HH:MM"
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    z = ZoneInfo(zone, tzpath=[tzpath])
    if fold is None:
        return dt.replace(tzinfo=z)
    else:
        return dt.replace(tzinfo=z, fold=fold)


def offsets_for_both_folds(dt_str, zone, tzpath):
    # Try both folds; if offsets differ, ambiguous=True
    a0 = _aware_from_wall(dt_str, zone, tzpath, fold=0)
    a1 = _aware_from_wall(dt_str, zone, tzpath, fold=1)
    off0 = int(a0.utcoffset().total_seconds())
    off1 = int(a1.utcoffset().total_seconds())
    ambiguous = off0 != off1
    # Nonexistent hint: heuristic — if adding fold doesn't change offset and
    # the local time is around 02:xx on a known spring-forward day, it might be nonexistent.
    nonexistent_hint = False
    if not ambiguous and a0.hour in (0, 1, 2, 3):
        # Compare UTC→local→UTC roundtrip
        back = a0.astimezone(ZoneInfo(zone, tzpath=[tzpath])).replace(tzinfo=None)
        nonexistent_hint = back != a0.replace(tzinfo=None)
    return {
        "offsets": sorted(set([off0, off1])),
        "ambiguous": ambiguous,
        "nonexistent_hint": nonexistent_hint,
    }


def main():
    args = parse_args()
    samples = load_samples(args.samples)
    out_rows = []
    max_abs = 0
    fails = 0
    for s in samples:
        zone = s["zone"]
        dtstr = s["local_datetime"]
        note = s.get("note", "")
        old = offsets_for_both_folds(dtstr, zone, args.old_tzpath)
        new = offsets_for_both_folds(dtstr, zone, args.new_tzpath)
        # Compute minimal absolute difference across interpretations
        diffs = [abs(no - oo) for oo in old["offsets"] for no in new["offsets"]]
        diff_sec = min(diffs) if diffs else 0
        status = "PASS" if diff_sec <= args.threshold else "FAIL"
        if status == "FAIL":
            fails += 1
        max_abs = max(max_abs, diff_sec)
        out_rows.append(
            {
                "zone": zone,
                "local_datetime": dtstr,
                "note": note,
                "old_offset_seconds": "/".join(map(str, old["offsets"])),
                "new_offset_seconds": "/".join(map(str, new["offsets"])),
                "difference_seconds": diff_sec,
                "ambiguous_old": old["ambiguous"],
                "ambiguous_new": new["ambiguous"],
                "nonexistent_hint_old": old["nonexistent_hint"],
                "nonexistent_hint_new": new["nonexistent_hint"],
                "status": status,
            }
        )
    summary = {
        "tzdb_old_version": os.path.basename(args.old_tzpath) or "old",
        "tzdb_new_version": os.path.basename(args.new_tzpath) or "new",
        "num_cases": len(samples),
        "num_failures": fails,
        "max_abs_diff_seconds": max_abs,
    }
    # Write JSON
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cases": out_rows}, f, ensure_ascii=False, indent=2)
    # Write CSV
    with open(args.out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
