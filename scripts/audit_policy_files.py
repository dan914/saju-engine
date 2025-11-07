#!/usr/bin/env python3
"""Policy Files Audit Script

Analyzes all policy files across the repository to support consolidation planning.

Features:
- Discovers all policy directories
- Catalogs all policy files with metadata
- Detects duplicates by content hash
- Identifies actively used files
- Generates comprehensive audit report with ISO audit timestamp

Usage:
    python scripts/audit_policy_files.py
    python scripts/audit_policy_files.py --output policy_audit.json
    python scripts/audit_policy_files.py --audit-date 2024-01-02
"""

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def find_policy_directories(repo_root: Path) -> List[Path]:
    """Find all directories named 'policies' in the repository."""
    policy_dirs = []

    # Add root-level policy directory if it exists
    root_policy = repo_root / "policy"
    if root_policy.is_dir():
        policy_dirs.append(root_policy)

    # Search for subdirectories named "policies"
    for path in repo_root.rglob("policies"):
        if path.is_dir() and not any(p.name.startswith(".") for p in path.parents):
            policy_dirs.append(path)

    return sorted(policy_dirs)


def catalog_policy_files(policy_dir: Path, repo_root: Path) -> List[Dict]:
    """Catalog all JSON files in a policy directory."""
    files = []
    for json_file in policy_dir.glob("*.json"):
        try:
            try:
                relative_path = json_file.relative_to(repo_root)
            except ValueError:
                relative_path = json_file
            file_info = {
                "name": json_file.name,
                "path": str(relative_path),
                "size": json_file.stat().st_size,
                "modified": json_file.stat().st_mtime,
                "hash": compute_file_hash(json_file),
            }
            files.append(file_info)
        except Exception as e:
            print(f"⚠️  Error processing {json_file}: {e}")
    return files


def find_file_references(repo_root: Path, filename: str) -> List[str]:
    """Find all code references to a policy file."""
    references = []

    # Search patterns
    patterns = [
        f'"{filename}"',
        f"'{filename}'",
        f"resolve_policy_path({filename})",
        f"load_policy_json({filename})",
    ]

    # Search in Python files
    for py_file in repo_root.rglob("*.py"):
        if any(p.name.startswith(".") for p in py_file.parents):
            continue
        if "tests" in py_file.parts or "test_" in py_file.name:
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            if filename in content:
                references.append(str(py_file.relative_to(repo_root)))
        except Exception:
            pass

    return references


def detect_duplicates(all_files: List[Dict]) -> Dict[str, List[Dict]]:
    """Detect duplicate files by content hash."""
    hash_groups = defaultdict(list)
    for file_info in all_files:
        hash_groups[file_info["hash"]].append(file_info)

    # Return only groups with duplicates
    return {h: files for h, files in hash_groups.items() if len(files) > 1}


def _resolve_audit_date(value: Optional[str]) -> str:
    """Return ISO-formatted audit date, validating overrides."""

    if not value:
        return datetime.now(UTC).date().isoformat()

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("audit_date must be ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)") from exc

    return parsed.date().isoformat()


def generate_audit_report(
    repo_root: Path,
    output_file: str = None,
    audit_date: Optional[str] = None,
) -> Dict:
    """Generate comprehensive audit report."""

    print("📊 Policy Files Audit Report")
    print("=" * 80)

    # Step 1: Find all policy directories
    print("\n🔍 Step 1: Discovering policy directories...")
    policy_dirs = find_policy_directories(repo_root)
    print(f"   Found {len(policy_dirs)} policy directories:")
    for i, pdir in enumerate(policy_dirs, 1):
        rel_path = pdir.relative_to(repo_root)
        print(f"   {i:2d}. {rel_path}")

    # Step 2: Catalog all files
    print("\n📁 Step 2: Cataloging policy files...")
    all_files = []
    dir_inventory = {}

    for policy_dir in policy_dirs:
        rel_dir = str(policy_dir.relative_to(repo_root))
        files = catalog_policy_files(policy_dir, repo_root)
        dir_inventory[rel_dir] = files
        all_files.extend(files)
        print(f"   {rel_dir}: {len(files)} files")

    print(f"\n   Total policy files: {len(all_files)}")

    # Step 3: Detect duplicates
    print("\n🔎 Step 3: Detecting duplicates...")
    duplicates = detect_duplicates(all_files)

    if duplicates:
        print(f"   Found {len(duplicates)} duplicate groups:")
        for i, (hash_val, files) in enumerate(duplicates.items(), 1):
            print(f"\n   Group {i} ({len(files)} copies):")
            for f in files:
                print(f"      - {f['path']}")
    else:
        print("   No duplicates found! ✨")

    # Step 4: Check for file usage
    print("\n🔗 Step 4: Analyzing file usage...")
    file_usage = {}
    unique_filenames = set(f["name"] for f in all_files)

    for filename in sorted(unique_filenames):
        references = find_file_references(repo_root, filename)
        file_usage[filename] = {
            "reference_count": len(references),
            "references": references,
            "status": "active" if references else "orphaned"
        }

    active_count = sum(1 for u in file_usage.values() if u["status"] == "active")
    orphaned_count = len(file_usage) - active_count

    print(f"   Active files (referenced in code): {active_count}")
    print(f"   Orphaned files (no references): {orphaned_count}")

    if orphaned_count > 0:
        print("\n   ⚠️  Orphaned files:")
        for filename, usage in file_usage.items():
            if usage["status"] == "orphaned":
                print(f"      - {filename}")

    # Step 5: Compile report
    report = {
        "audit_date": _resolve_audit_date(audit_date),
        "repo_root": str(repo_root),
        "summary": {
            "total_directories": len(policy_dirs),
            "total_files": len(all_files),
            "unique_files": len(unique_filenames),
            "duplicate_groups": len(duplicates),
            "active_files": active_count,
            "orphaned_files": orphaned_count,
        },
        "directories": {
            rel_dir: {
                "file_count": len(files),
                "files": [f["name"] for f in files]
            }
            for rel_dir, files in dir_inventory.items()
        },
        "duplicates": {
            f"group_{i}": {
                "hash": hash_val,
                "copies": len(files),
                "locations": [f["path"] for f in files]
            }
            for i, (hash_val, files) in enumerate(duplicates.items(), 1)
        },
        "file_usage": file_usage,
        "all_files": all_files,
    }

    # Save report
    if output_file:
        output_path = repo_root / output_file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Report saved to: {output_path}")

    print("\n" + "=" * 80)
    print("✅ Audit complete!")

    return report


def main():
    parser = argparse.ArgumentParser(description="Audit policy files in repository")
    parser.add_argument(
        "--output",
        "-o",
        default="docs/policy_audit.json",
        help="Output file for audit report (default: docs/policy_audit.json)"
    )
    parser.add_argument(
        "--repo-root",
        "-r",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Repository root directory"
    )
    parser.add_argument(
        "--audit-date",
        type=str,
        help="Override audit date (ISO 8601). Defaults to current UTC date.",
    )

    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    print(f"Repository root: {repo_root}\n")

    try:
        generate_audit_report(repo_root, args.output, audit_date=args.audit_date)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
