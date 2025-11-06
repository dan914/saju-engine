"""
Monorepo Python path bootstrap for saju-engine.

This file is automatically loaded by Python on startup and adds
all service directories to sys.path so that 'from app.main import app'
works from anywhere in the monorepo.

Auto-loaded by: poetry run python, poetry run pytest, poetry shell, etc.

Installation:
    poetry run python scripts/setup_dev_environment.py

Design:
    - Placed in virtualenv's site-packages by setup script
    - Uses relative path calculation from repo root marker (pyproject.toml)
    - Idempotent: safe to run multiple times
    - No dependencies: pure stdlib only

Path Resolution Strategy:
    1. Find site-packages directory (where this file lives)
    2. Search upward for repo root (contains pyproject.toml)
    3. Add service directories relative to repo root
    4. Deduplicate paths to avoid conflicts

Service Paths Added:
    - services/analysis-service
    - services/api-gateway
    - services/pillars-service
    - services/astro-service
    - services/tz-time-service
    - services/llm-polish
    - services/llm-checker
    - services/common

Version: 1.0.0
Last Updated: 2025-11-04
"""
import sys
from pathlib import Path


def _find_repo_root(start_path: Path) -> Path | None:
    """
    Find repository root by searching for pyproject.toml.

    Searches upward from start_path until finding pyproject.toml
    or hitting filesystem root.

    Args:
        start_path: Directory to start searching from

    Returns:
        Path to repo root if found, None otherwise
    """
    current = start_path.resolve()

    # Search up to 10 levels to avoid infinite loops
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current

        parent = current.parent
        if parent == current:  # Hit filesystem root
            return None

        current = parent

    return None


def _bootstrap_monorepo_paths() -> None:
    """
    Add all monorepo service directories to sys.path.

    This function:
    1. Finds the repo root (contains pyproject.toml)
    2. Adds each service directory to sys.path
    3. Deduplicates to avoid conflicts
    4. Runs silently unless DEBUG_BOOTSTRAP is set
    """
    # Find repo root
    site_packages = Path(__file__).parent
    repo_root = _find_repo_root(site_packages)

    if repo_root is None:
        # Silent failure - don't break imports if repo structure changes
        return

    # Define service directories
    service_dirs = [
        "services/analysis-service",
        "services/api-gateway",
        "services/pillars-service",
        "services/astro-service",
        "services/tz-time-service",
        "services/llm-polish",
        "services/llm-checker",
        "services/common",
    ]

    # Add service paths
    added_count = 0
    for service_dir in service_dirs:
        service_path = repo_root / service_dir

        if not service_path.exists():
            continue  # Skip missing services (development in progress)

        service_path_str = str(service_path)

        # Deduplicate - only add if not already in path
        if service_path_str not in sys.path:
            sys.path.insert(0, service_path_str)
            added_count += 1

    # Optional debug output
    import os
    if os.getenv("DEBUG_BOOTSTRAP"):
        print(f"[sitecustomize] Added {added_count} service paths from {repo_root}")


# Run bootstrap on module import
_bootstrap_monorepo_paths()
