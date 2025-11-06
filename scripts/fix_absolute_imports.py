#!/usr/bin/env python3
"""Fix absolute 'from app.' imports to relative imports.

This script replaces absolute imports like:
    from app.core.engine import AnalysisEngine

With relative imports like:
    from .engine import AnalysisEngine

This allows services to work without sitecustomize.py path hacks.

Usage:
    python scripts/fix_absolute_imports.py services/analysis-service/
    python scripts/fix_absolute_imports.py --dry-run services/analysis-service/
"""

import argparse
import re
import sys
from pathlib import Path


def fix_imports_in_file(file_path: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Fix absolute app imports in a single file.

    Args:
        file_path: Path to Python file
        dry_run: If True, only report changes without modifying

    Returns:
        Tuple of (num_changes, list_of_changes)
    """
    try:
        content = file_path.read_text()
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}", file=sys.stderr)
        return 0, []

    # Pattern: from app.core.something import ...
    # Replace with: from .something import ...
    pattern = re.compile(r'^from app\.core\.(\S+)', re.MULTILINE)

    changes = []
    new_content = content

    for match in pattern.finditer(content):
        full_line = match.group(0)
        module_name = match.group(1)
        new_line = f"from .{module_name}"

        changes.append(f"  {full_line} → {new_line}")
        new_content = new_content.replace(full_line, new_line, 1)

    if changes and not dry_run:
        try:
            file_path.write_text(new_content)
            print(f"✅ Fixed {len(changes)} imports in {file_path}")
        except Exception as e:
            print(f"⚠️  Error writing {file_path}: {e}", file=sys.stderr)
            return 0, []

    return len(changes), changes


def fix_imports_in_directory(directory: Path, dry_run: bool = False) -> dict:
    """Fix imports in all Python files in a directory.

    Args:
        directory: Root directory to scan
        dry_run: If True, only report changes without modifying

    Returns:
        Dictionary with statistics
    """
    stats = {
        "files_scanned": 0,
        "files_modified": 0,
        "total_changes": 0,
        "changes_by_file": {},
    }

    for py_file in directory.rglob("*.py"):
        # Skip __pycache__ and .venv
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue

        stats["files_scanned"] += 1
        num_changes, changes = fix_imports_in_file(py_file, dry_run=dry_run)

        if num_changes > 0:
            stats["files_modified"] += 1
            stats["total_changes"] += num_changes
            stats["changes_by_file"][str(py_file)] = changes

    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix absolute 'from app.' imports to relative imports"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory to scan for Python files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )

    args = parser.parse_args()

    if not args.directory.exists():
        print(f"❌ Directory not found: {args.directory}", file=sys.stderr)
        return 1

    if not args.directory.is_dir():
        print(f"❌ Not a directory: {args.directory}", file=sys.stderr)
        return 1

    print(f"🔍 Scanning {args.directory} for absolute imports...")
    if args.dry_run:
        print("   (DRY RUN - no files will be modified)")
    print()

    stats = fix_imports_in_directory(args.directory, dry_run=args.dry_run)

    print()
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   Files scanned: {stats['files_scanned']}")
    print(f"   Files modified: {stats['files_modified']}")
    print(f"   Total changes: {stats['total_changes']}")

    if stats["changes_by_file"]:
        print()
        print("📝 Changes by file:")
        for file_path, changes in stats["changes_by_file"].items():
            print(f"\n   {file_path}:")
            for change in changes:
                print(change)

    if args.dry_run and stats["total_changes"] > 0:
        print()
        print("💡 Run without --dry-run to apply these changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
