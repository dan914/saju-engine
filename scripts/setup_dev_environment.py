#!/usr/bin/env python3
"""
Setup development environment for saju-engine monorepo.

This script creates a .pth file in the virtualenv's site-packages
to automatically add all service directories to sys.path.

Usage:
    poetry run python scripts/setup_dev_environment.py

Note:
    We use .pth files instead of sitecustomize.py because system-level
    sitecustomize.py (/usr/lib/python3.12/) takes precedence over
    virtualenv-level sitecustomize.py, preventing our customizations
    from loading. .pth files work reliably in all environments.
"""
from __future__ import annotations

import site
import sys
from pathlib import Path


def main() -> None:
    """Set up .pth file for monorepo service imports."""

    # Get repo root (parent of scripts/)
    repo_root = Path(__file__).parent.parent.resolve()

    # Get site-packages directory
    try:
        site_packages = Path(site.getsitepackages()[0])
    except (IndexError, AttributeError):
        print("❌ Error: Could not find site-packages directory")
        print("   Make sure you're running this inside a Poetry virtualenv")
        sys.exit(1)

    # Service directory list
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

    # Create .pth file content with absolute paths
    pth_content = "\n".join(
        str(repo_root / service_dir) for service_dir in service_dirs
    )

    # Write .pth file
    pth_file = site_packages / "saju_services.pth"
    pth_file.write_text(pth_content, encoding="utf-8")

    print(f"✅ Created {pth_file}")
    print(f"\n📦 Added {len(service_dirs)} service paths:")
    for service_dir in service_dirs:
        status = "✅" if (repo_root / service_dir).exists() else "⚠️"
        print(f"   {status} {service_dir}")

    print("\n✅ Development environment configured!")
    print("\n🎯 Next steps:")
    print("   1. Verify: poetry run python scripts/verify_dev_setup.py")
    print("   2. Test imports: poetry run python -c 'from app.main import app'")
    print("   3. Run tests: poetry run pytest services/analysis-service/tests/")


if __name__ == "__main__":
    main()
