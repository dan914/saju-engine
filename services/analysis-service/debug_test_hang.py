#!/usr/bin/env python3
"""
Diagnostic script to debug test hang issue.

This script helps identify why tests might hang in different environments.
Run this BEFORE running pytest to see where the issue might be.
"""

import sys
import time
from pathlib import Path

print("=" * 80)
print("TEST HANG DIAGNOSTIC SCRIPT")
print("=" * 80)

# 1. Check Python environment
print("\n1. PYTHON ENVIRONMENT:")
print(f"   Python version: {sys.version}")
print(f"   Python executable: {sys.executable}")
print(f"   Current working directory: {Path.cwd()}")

# 2. Check if we can import the app without hanging
print("\n2. ATTEMPTING TO IMPORT APP MODULES:")
start = time.time()

try:
    print("   Importing pathlib and sys... ", end="", flush=True)
    from pathlib import Path
    import sys
    elapsed = time.time() - start
    print(f"OK ({elapsed:.3f}s)")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

# 3. Check sys.path setup
print("\n3. CHECKING SYS.PATH SETUP:")
start = time.time()
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[4]
    SERVICES_ROOT = PROJECT_ROOT / "services"
    SERVICE_ROOT = Path(__file__).resolve().parents[1]

    paths_to_add = [SERVICES_ROOT, PROJECT_ROOT, SERVICE_ROOT]
    for path in reversed(paths_to_add):
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))

    elapsed = time.time() - start
    print(f"   Path setup completed ({elapsed:.3f}s)")
    print(f"   PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"   SERVICES_ROOT: {SERVICES_ROOT}")
    print(f"   SERVICE_ROOT: {SERVICE_ROOT}")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

# 4. Try importing app.main (this triggers startup)
print("\n4. IMPORTING APP.MAIN (this loads policy files):")
start = time.time()
try:
    print("   Importing app.main... ", end="", flush=True)
    from app.main import app
    elapsed = time.time() - start
    print(f"OK ({elapsed:.3f}s)")
except Exception as e:
    elapsed = time.time() - start
    print(f"FAILED after {elapsed:.3f}s")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Check if dependencies can be preloaded
print("\n5. PRELOADING DEPENDENCIES (mimics startup):")
start = time.time()
try:
    print("   Importing dependencies module... ", end="", flush=True)
    from app.api.dependencies import preload_dependencies
    elapsed = time.time() - start
    print(f"OK ({elapsed:.3f}s)")

    print("   Calling preload_dependencies()... ", end="", flush=True)
    start = time.time()
    preload_dependencies()
    elapsed = time.time() - start
    print(f"OK ({elapsed:.3f}s)")
except Exception as e:
    elapsed = time.time() - start
    print(f"FAILED after {elapsed:.3f}s")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. Check policy file access
print("\n6. CHECKING POLICY FILE ACCESS:")
start = time.time()
try:
    from app.core.korean_enricher import (
        REPO_ROOT,
        POLICY_DIR,
        LOCALIZATION_KO_PATH,
        GYEOKGUK_POLICY_PATH,
        SHENSHA_POLICY_PATH,
        JIAZI_POLICY_PATH,
    )

    print(f"   REPO_ROOT: {REPO_ROOT}")
    print(f"   POLICY_DIR: {POLICY_DIR}")
    print(f"   POLICY_DIR exists: {POLICY_DIR.exists()}")

    policy_files = [
        ("localization_ko_v1.json", LOCALIZATION_KO_PATH),
        ("gyeokguk_policy.json", GYEOKGUK_POLICY_PATH),
        ("shensha_v2_policy.json", SHENSHA_POLICY_PATH),
        ("sixty_jiazi.json", JIAZI_POLICY_PATH),
    ]

    for name, path in policy_files:
        exists = path.exists()
        readable = path.is_file() if exists else False
        print(f"   {name}: exists={exists}, readable={readable}")
        if not exists:
            print(f"      Expected at: {path}")

    elapsed = time.time() - start
    print(f"   Policy file check completed ({elapsed:.3f}s)")
except Exception as e:
    elapsed = time.time() - start
    print(f"   FAILED after {elapsed:.3f}s")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 7. Try creating a test client
print("\n7. CREATING TEST CLIENT:")
start = time.time()
try:
    print("   Importing TestClient... ", end="", flush=True)
    from fastapi.testclient import TestClient
    elapsed = time.time() - start
    print(f"OK ({elapsed:.3f}s)")

    print("   Creating TestClient instance... ", end="", flush=True)
    start = time.time()
    client = TestClient(app, raise_server_exceptions=True)
    elapsed = time.time() - start
    print(f"OK ({elapsed:.3f}s)")

    print("   Client created successfully!")
except Exception as e:
    elapsed = time.time() - start
    print(f"FAILED after {elapsed:.3f}s")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE - No hangs detected!")
print("=" * 80)
print("\nIf pytest hangs but this script doesn't, the issue may be:")
print("  1. Pytest-specific configuration or plugins")
print("  2. Test fixture initialization in conftest.py")
print("  3. Different Python path resolution in pytest")
print("  4. Async event loop issues in pytest")
print("\nSuggested next steps:")
print("  1. Run: pytest tests/test_analyze.py -v -s --tb=short")
print("  2. Run with debugging: pytest tests/test_analyze.py -v -s --pdb")
print("  3. Check for hanging fixtures: pytest tests/test_analyze.py --setup-show")
