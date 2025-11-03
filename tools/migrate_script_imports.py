#!/usr/bin/env python3
"""Automated migration tool for converting sys.path hacks to Poetry-based imports.

This tool analyzes Python scripts and suggests/applies migrations from:
    sys.path.insert() + from app.X import Y
To:
    from scripts._script_loader import get_*_module
    Y = get_*_module("X", "Y")

Usage:
    # Dry run (show changes without applying)
    poetry run python tools/migrate_script_imports.py scripts/your_script.py

    # Apply changes
    poetry run python tools/migrate_script_imports.py --apply scripts/your_script.py

    # Batch process directory
    poetry run python tools/migrate_script_imports.py --apply scripts/*.py

    # Batch process all eligible files
    poetry run python tools/migrate_script_imports.py --apply --all
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

# ANSI colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def find_sys_path_inserts(content: str) -> List[str]:
    """Find all sys.path.insert() or sys.path.append() lines."""
    pattern = r'sys\.path\.(insert|append)\([^)]+\)'
    return re.findall(pattern, content)


def find_app_imports(content: str) -> List[Tuple[str, str, str]]:
    """Find all 'from app.X import Y' style imports.

    Returns list of (full_line, module_path, imported_names)
    """
    pattern = r'from\s+app\.([a-z_.]+)\s+import\s+(.+?)(?:\n|$)'
    matches = []
    for match in re.finditer(pattern, content):
        full_line = match.group(0).strip()
        module_path = match.group(1)
        imported_names = match.group(2).strip()
        matches.append((full_line, module_path, imported_names))
    return matches


def determine_service(module_path: str) -> str:
    """Determine which service loader to use based on module path."""
    if module_path.startswith("core.") or module_path.startswith("models."):
        # Need to check context - default to analysis
        return "analysis"
    return "analysis"  # Default assumption


def generate_loader_import(imports: List[Tuple[str, str, str]]) -> str:
    """Generate the script_loader import statement."""
    services = set()
    for _, module_path, _ in imports:
        service = determine_service(module_path)
        services.add(service)

    loaders = [f"get_{svc}_module" for svc in sorted(services)]
    return f"from scripts._script_loader import {', '.join(loaders)}"


def convert_import_to_loader(module_path: str, imported_names: str, service: str = "analysis") -> List[str]:
    """Convert an import statement to loader calls.

    Args:
        module_path: e.g., "core.engine" or "models.analysis"
        imported_names: e.g., "AnalysisEngine" or "AnalysisRequest, AnalysisResponse"
        service: "analysis", "pillars", etc.

    Returns:
        List of loader call lines
    """
    # Extract module name (last part of path)
    parts = module_path.split(".")
    module_name = parts[-1] if len(parts) > 1 else module_path

    # Parse imported names
    names = [name.strip() for name in imported_names.split(",")]

    # Generate loader calls
    loader_calls = []
    for name in names:
        # Handle "X as Y" aliases
        if " as " in name:
            actual_name, alias = name.split(" as ")
            actual_name = actual_name.strip()
            alias = alias.strip()
            loader_calls.append(
                f'{alias} = get_{service}_module("{module_name}", "{actual_name}")'
            )
        else:
            name = name.strip()
            loader_calls.append(
                f'{name} = get_{service}_module("{module_name}", "{name}")'
            )

    return loader_calls


def migrate_script(file_path: Path, apply: bool = False) -> Tuple[str, int]:
    """Migrate a single script file.

    Returns:
        (status_message, changes_count)
    """
    content = file_path.read_text()
    original_content = content

    # Check if already migrated
    if "scripts._script_loader" in content:
        return f"{YELLOW}Already migrated{RESET}", 0

    # Find sys.path manipulations
    sys_paths = find_sys_path_inserts(content)
    if not sys_paths:
        return f"{BLUE}No sys.path found{RESET}", 0

    # Find app imports
    app_imports = find_app_imports(content)
    if not app_imports:
        return f"{YELLOW}Has sys.path but no app imports{RESET}", 0

    # Build new content
    lines = content.splitlines(keepends=True)
    new_lines = []
    skip_next_blank = False
    loader_import_added = False
    loader_calls = []

    # Collect all loader calls
    for full_line, module_path, imported_names in app_imports:
        service = determine_service(module_path)
        calls = convert_import_to_loader(module_path, imported_names, service)
        loader_calls.extend(calls)

    for i, line in enumerate(lines):
        # Skip sys.path lines
        if "sys.path." in line and ("insert" in line or "append" in line):
            skip_next_blank = True
            continue

        # Skip blank lines after sys.path (cleanup)
        if skip_next_blank and line.strip() == "":
            skip_next_blank = False
            continue
        skip_next_blank = False

        # Replace app imports with loader calls
        if line.strip().startswith("from app."):
            # Add loader import if not added yet
            if not loader_import_added:
                new_lines.append("\n")
                new_lines.append("# Use Poetry-based imports via script loader\n")
                loader_import = generate_loader_import(app_imports)
                new_lines.append(f"{loader_import}\n")
                new_lines.append("\n")
                new_lines.append("# Load required classes/functions from services\n")
                for call in loader_calls:
                    new_lines.append(f"{call}\n")
                loader_import_added = True
            # Skip the original import line
            continue

        # Keep all other lines
        new_lines.append(line)

    new_content = "".join(new_lines)

    # Show diff
    changes_count = len(sys_paths) + len(app_imports)

    if apply:
        file_path.write_text(new_content)
        return f"{GREEN}✓ Migrated{RESET}", changes_count
    else:
        print(f"\n{BLUE}Preview for {file_path}:{RESET}")
        print(f"  {RED}- Remove {len(sys_paths)} sys.path lines{RESET}")
        print(f"  {RED}- Remove {len(app_imports)} app import lines{RESET}")
        print(f"  {GREEN}+ Add script_loader import{RESET}")
        print(f"  {GREEN}+ Add {len(loader_calls)} loader calls{RESET}")
        return f"{YELLOW}Not applied (dry run){RESET}", changes_count


def find_eligible_files() -> List[Path]:
    """Find all Python files with sys.path manipulation."""
    root = Path(__file__).resolve().parents[1]
    eligible = []

    # Search in scripts/ and run_*.py
    for pattern in ["scripts/*.py", "run_*.py", "tools/*.py"]:
        for file_path in root.glob(pattern):
            if file_path.name.startswith("_"):
                continue
            content = file_path.read_text()
            if "sys.path." in content and ("insert" in content or "append" in content):
                eligible.append(file_path)

    return sorted(eligible)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate scripts from sys.path hacks to Poetry-based imports"
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Script files to migrate (or use --all)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default is dry run)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all eligible files"
    )

    args = parser.parse_args()

    # Determine files to process
    if args.all:
        files = find_eligible_files()
        print(f"{BLUE}Found {len(files)} eligible files{RESET}\n")
    elif args.files:
        files = args.files
    else:
        parser.print_help()
        sys.exit(1)

    # Process each file
    total_changes = 0
    for file_path in files:
        status, changes = migrate_script(file_path, apply=args.apply)
        print(f"{file_path.name:50s} {status} ({changes} changes)")
        total_changes += changes

    # Summary
    print(f"\n{BLUE}Summary:{RESET}")
    print(f"  Files processed: {len(files)}")
    print(f"  Total changes: {total_changes}")

    if not args.apply:
        print(f"\n{YELLOW}This was a dry run. Use --apply to make changes.{RESET}")
    else:
        print(f"\n{GREEN}Migration complete! Test with: poetry run python <script>{RESET}")


if __name__ == "__main__":
    main()
