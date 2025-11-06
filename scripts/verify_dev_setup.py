#!/usr/bin/env python3
"""
Verify development environment is correctly set up.

This script checks that:
1. .pth file exists and is correctly configured
2. Service paths are in sys.path
3. Imports work from repo root
4. FastAPI TestClient works

Usage:
    poetry run python scripts/verify_dev_setup.py
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Verify development setup."""

    print("=" * 70)
    print("DEVELOPMENT ENVIRONMENT VERIFICATION")
    print("=" * 70)

    success = True

    # Check 1: .pth file exists
    print("\n✓ Checking .pth file...")
    try:
        import site
        site_packages = Path(site.getsitepackages()[0])
        pth_file = site_packages / "saju_services.pth"

        if pth_file.exists():
            print(f"  ✅ Found: {pth_file}")
            lines = pth_file.read_text().strip().split("\n")
            print(f"  ✅ Contains {len(lines)} service paths")
        else:
            print(f"  ❌ NOT FOUND: {pth_file}")
            print("  ⚠️  Run: poetry run python scripts/setup_dev_environment.py")
            success = False
    except Exception as e:
        print(f"  ❌ Error checking .pth file: {e}")
        success = False

    # Check 2: Service paths in sys.path
    print("\n✓ Checking sys.path...")
    service_paths = [p for p in sys.path if "services/" in p and "saju-engine" in p]

    if len(service_paths) >= 8:
        print(f"  ✅ Found {len(service_paths)} service paths in sys.path")
        for path in service_paths[:3]:
            service_name = path.split("/")[-1]
            print(f"     - {service_name}")
        if len(service_paths) > 3:
            print(f"     ... and {len(service_paths) - 3} more")
    else:
        print(f"  ❌ Only found {len(service_paths)} service paths (expected 8)")
        print("  ⚠️  Run: poetry run python scripts/setup_dev_environment.py")
        success = False

    # Check 3: Test import
    print("\n✓ Testing import from analysis-service...")
    try:
        from app.main import app
        print(f"  ✅ Successfully imported: {type(app).__name__}")
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        print("  ⚠️  Run: poetry run python scripts/setup_dev_environment.py")
        success = False

    # Check 4: Test FastAPI TestClient
    print("\n✓ Testing FastAPI TestClient...")
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/health")
        payload = response.json()

        if response.status_code == 200:
            print(f"  ✅ Health check passed")
            print(f"     Service: {payload.get('app', 'unknown')}")
            print(f"     Version: {payload.get('version', 'unknown')}")
        else:
            print(f"  ❌ Health check returned {response.status_code}")
            success = False
    except Exception as e:
        print(f"  ❌ TestClient failed: {e}")
        success = False

    # Final result
    print("\n" + "=" * 70)
    if success:
        print("🎉 ALL CHECKS PASSED!")
        print("=" * 70)
        print("\n✅ Your development environment is correctly set up.")
        print("✅ You can now run:")
        print("   - poetry run python -c 'from app.main import app'")
        print("   - poetry run pytest services/analysis-service/tests/")
        print("   - poetry run python scripts/any_script.py")
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 70)
        print("\n⚠️  Your development environment needs setup.")
        print("⚠️  Run: poetry run python scripts/setup_dev_environment.py")
        print("⚠️  Then run this script again to verify.")
        sys.exit(1)


if __name__ == "__main__":
    main()
