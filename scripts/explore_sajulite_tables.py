#!/usr/bin/env python3
"""
Explore Saju Lite database structure - list all tables and their basic info.
"""
import json
from pathlib import Path


def explore_file(filepath: Path):
    """Explore a single JSON file."""
    print(f"\n{'='*100}")
    print(f"FILE: {filepath.name}")
    print(f"Size: {filepath.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"{'='*100}\n")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables = []
    for table_name, rows in data.items():
        if isinstance(rows, list):
            row_count = len(rows)
            columns = list(rows[0].keys()) if rows else []

            # Get sample data
            sample = rows[0] if rows else {}
            sample_str = json.dumps(sample, ensure_ascii=False)[:150]

            tables.append(
                {
                    "name": table_name,
                    "rows": row_count,
                    "cols": len(columns),
                    "columns": columns,
                    "sample": sample_str,
                }
            )

    # Sort by row count descending
    tables.sort(key=lambda x: x["rows"], reverse=True)

    print(f"{'TABLE NAME':<40} {'ROWS':>8} {'COLS':>6} {'COLUMN NAMES'}")
    print(f"{'-'*100}")

    for t in tables:
        col_preview = ", ".join(t["columns"][:5])
        if len(t["columns"]) > 5:
            col_preview += f", ... (+{len(t['columns']) - 5})"
        print(f"{t['name']:<40} {t['rows']:>8} {t['cols']:>6} {col_preview}")

    # Now print detailed info for each table
    print(f"\n{'='*100}")
    print("DETAILED TABLE INFORMATION")
    print(f"{'='*100}\n")

    for t in tables:
        print(f"\n{'─'*100}")
        print(f"TABLE: {t['name']}")
        print(f"Rows: {t['rows']}, Columns: {t['cols']}")
        print(f"{'─'*100}")
        print(f"Columns: {', '.join(t['columns'])}")
        print(f"\nFirst row sample:")
        print(f"  {t['sample']}")


def main():
    base_path = Path("/Users/yujumyeong/Downloads/sajulite_data")

    files = ["sajulite_complete_data.json", "sajulite_db5_data.json", "sajulite_unsedb_data.json"]

    for filename in files:
        filepath = base_path / filename
        if filepath.exists():
            explore_file(filepath)
        else:
            print(f"⚠️  File not found: {filepath}")


if __name__ == "__main__":
    main()
