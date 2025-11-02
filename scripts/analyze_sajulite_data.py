#!/usr/bin/env python3
"""
Analyze Saju Lite database files to find missing feature data.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Keywords for each feature category
SEARCH_PATTERNS = {
    "12_lifecycle": {
        "keywords": [
            # Chinese characters
            "長生",
            "沐浴",
            "冠帶",
            "臨官",
            "帝旺",
            "衰",
            "病",
            "死",
            "墓",
            "絕",
            "胎",
            "養",
            # Korean
            "장생",
            "목욕",
            "관대",
            "임관",
            "제왕",
            "사",
            "병",
            "묘",
            "절",
            "태",
            "양",
            # Terms
            "12운성",
            "십이운성",
            "lifecycle",
            "unse",
            "운세",
        ],
        "table_patterns": ["unse", "12un", "lifecycle", "saju", "psaju", "fsaju"],
        "expected_rows": [60, 120, 240],  # Possible combinations
    },
    "five_elements": {
        "keywords": [
            "木",
            "火",
            "土",
            "金",
            "水",
            "목",
            "화",
            "토",
            "금",
            "수",
            "오행",
            "element",
            "분석",
            "발달",
            "적정",
            "과다",
            "부족",
        ],
        "table_patterns": ["element", "오행", "ohang", "analysis"],
        "expected_rows": None,
    },
    "branch_tengods": {
        "keywords": ["지지", "십성", "地支", "十神", "branch", "tengod"],
        "table_patterns": ["jiji", "branch", "tengod", "sipsung"],
        "expected_rows": [12, 60, 120],
    },
    "luck_pillars": {
        "keywords": ["대운", "daeun", "luck", "六十甲子", "60갑자", "pillar", "period"],
        "table_patterns": ["daeun", "luck", "period", "gapja"],
        "expected_rows": [60, 120],
    },
    "yongshin": {
        "keywords": [
            "용신",
            "yongshin",
            "억부",
            "조후",
            "통관",
            "beneficial",
            "元神",
            "喜神",
            "忌神",
        ],
        "table_patterns": ["yong", "beneficial", "god"],
        "expected_rows": None,
    },
    "divine_stars": {
        "keywords": [
            "신살",
            "shensha",
            "귀인",
            "역마",
            "도화",
            "괴강",
            "천을",
            "문창",
            "divine",
            "star",
            "神殺",
        ],
        "table_patterns": ["sinsal", "shensha", "star", "gwiin"],
        "expected_rows": None,
    },
    "hidden_stems": {
        "keywords": ["지장간", "zanggan", "hidden", "stem", "藏干"],
        "table_patterns": ["zanggan", "jijanggan", "hidden"],
        "expected_rows": [12, 36],
    },
}


def load_json_file(filepath: Path) -> Dict:
    """Load JSON file and return data."""
    print(f"\n{'='*80}")
    print(f"Loading: {filepath.name}")
    print(f"Size: {filepath.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"{'='*80}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def analyze_table(table_name: str, rows: List[Dict]) -> Dict[str, Any]:
    """Analyze a single table and return metadata."""
    if not rows:
        return {
            "row_count": 0,
            "columns": [],
            "sample_rows": [],
            "has_korean": False,
            "has_chinese": False,
        }

    row_count = len(rows)
    columns = list(rows[0].keys()) if rows else []
    sample_rows = rows[:5]

    # Check for Korean/Chinese characters
    all_text = json.dumps(sample_rows, ensure_ascii=False)
    has_korean = any("\uac00" <= c <= "\ud7a3" for c in all_text)
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in all_text)

    return {
        "row_count": row_count,
        "columns": columns,
        "sample_rows": sample_rows,
        "has_korean": has_korean,
        "has_chinese": has_chinese,
    }


def match_keywords(text: str, keywords: List[str]) -> List[str]:
    """Check if text contains any keywords."""
    text_lower = text.lower()
    matched = []
    for keyword in keywords:
        if keyword.lower() in text_lower or keyword in text:
            matched.append(keyword)
    return matched


def search_feature_in_data(data: Dict, feature_name: str, patterns: Dict) -> List[Dict]:
    """Search for a specific feature in the data."""
    results = []
    keywords = patterns["keywords"]
    table_patterns = patterns["table_patterns"]
    expected_rows = patterns.get("expected_rows")

    for table_name, rows in data.items():
        # Skip if not a list
        if not isinstance(rows, list):
            continue

        # Check table name for patterns
        table_name_lower = table_name.lower()
        table_matches = [p for p in table_patterns if p.lower() in table_name_lower]

        # Analyze table
        metadata = analyze_table(table_name, rows)

        # Check columns for keywords
        column_text = " ".join(metadata["columns"])
        column_matches = match_keywords(column_text, keywords)

        # Check sample data for keywords
        sample_text = json.dumps(metadata["sample_rows"], ensure_ascii=False)
        data_matches = match_keywords(sample_text, keywords)

        # Check row count
        row_count_match = False
        if expected_rows:
            row_count_match = metadata["row_count"] in expected_rows

        # Calculate relevance score
        score = 0
        if table_matches:
            score += 10
        if column_matches:
            score += 5
        if data_matches:
            score += 3
        if row_count_match:
            score += 5

        # Only include if there's some match
        if score > 0:
            results.append(
                {
                    "table_name": table_name,
                    "score": score,
                    "table_matches": table_matches,
                    "column_matches": column_matches,
                    "data_matches": data_matches,
                    "row_count_match": row_count_match,
                    "metadata": metadata,
                }
            )

    # Sort by score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def print_feature_results(feature_name: str, results: List[Dict]):
    """Print results for a feature."""
    print(f"\n{'='*80}")
    print(f"FEATURE: {feature_name.upper().replace('_', ' ')}")
    print(f"{'='*80}")

    if not results:
        print("❌ NOT FOUND - No matching tables")
        return

    for i, result in enumerate(results[:10], 1):  # Top 10 results
        metadata = result["metadata"]
        print(f"\n{'─'*80}")
        print(f"#{i} - {result['table_name']} (Score: {result['score']})")
        print(f"{'─'*80}")
        print(f"Row Count: {metadata['row_count']}")
        print(f"Columns: {', '.join(metadata['columns'][:10])}")
        if len(metadata["columns"]) > 10:
            print(f"         ... and {len(metadata['columns']) - 10} more")

        if result["table_matches"]:
            print(f"✓ Table name matches: {', '.join(result['table_matches'])}")
        if result["column_matches"]:
            print(f"✓ Column matches: {', '.join(result['column_matches'][:10])}")
        if result["data_matches"]:
            print(f"✓ Data matches: {', '.join(set(result['data_matches'][:10]))}")
        if result["row_count_match"]:
            print(f"✓ Row count matches expected pattern")

        print(f"\nKorean: {'Yes' if metadata['has_korean'] else 'No'}")
        print(f"Chinese: {'Yes' if metadata['has_chinese'] else 'No'}")

        # Print sample rows
        print(f"\nSample Data (first 3 rows):")
        for j, row in enumerate(metadata["sample_rows"][:3], 1):
            print(f"  Row {j}: {json.dumps(row, ensure_ascii=False)[:200]}")
            if len(json.dumps(row, ensure_ascii=False)) > 200:
                print(f"         ...")


def main():
    base_path = Path("/Users/yujumyeong/Downloads/sajulite_data")

    files = ["sajulite_complete_data.json", "sajulite_db5_data.json", "sajulite_unsedb_data.json"]

    # Store all results
    all_results = {}

    for filename in files:
        filepath = base_path / filename
        if not filepath.exists():
            print(f"⚠️  File not found: {filepath}")
            continue

        # Load data
        data = load_json_file(filepath)

        print(f"\nTotal tables: {len(data)}")

        # Search for each feature
        for feature_name, patterns in SEARCH_PATTERNS.items():
            print(f"\nSearching for: {feature_name}...")
            results = search_feature_in_data(data, feature_name, patterns)

            if filename not in all_results:
                all_results[filename] = {}
            all_results[filename][feature_name] = results

    # Print comprehensive report
    print("\n" + "=" * 80)
    print("COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 80)

    for filename, features in all_results.items():
        print(f"\n\n{'#'*80}")
        print(f"FILE: {filename}")
        print(f"{'#'*80}")

        for feature_name, results in features.items():
            print_feature_results(feature_name, results)

    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for filename, features in all_results.items():
        print(f"\n{filename}:")
        for feature_name, results in features.items():
            if results:
                status = "✅ FOUND" if results[0]["score"] >= 10 else "🟡 PARTIAL"
                top_table = results[0]["table_name"]
                row_count = results[0]["metadata"]["row_count"]
                print(f"  {status:12} {feature_name:20} - {top_table} ({row_count} rows)")
            else:
                print(f"  ❌ NOT FOUND {feature_name:20}")


if __name__ == "__main__":
    main()
