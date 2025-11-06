"""
Customize Python path for monorepo services.

This file is automatically loaded by Python on startup and adds
all service directories to sys.path so that 'from app.main import app'
works from the repo root.

Loaded by: poetry run python, poetry run pytest, etc.
"""
import sys
from pathlib import Path

# Get repo root (where this file lives)
REPO_ROOT = Path(__file__).parent

# Add service directories to Python path
SERVICE_DIRS = [
    REPO_ROOT,
    REPO_ROOT / "services" / "analysis-service",
    REPO_ROOT / "services" / "api-gateway",
    REPO_ROOT / "services" / "pillars-service",
    REPO_ROOT / "services" / "astro-service",
    REPO_ROOT / "services" / "tz-time-service",
    REPO_ROOT / "services" / "llm-polish",
    REPO_ROOT / "services" / "llm-checker",
    REPO_ROOT / "services" / "common",
]

for service_dir in SERVICE_DIRS:
    service_path = str(service_dir)
    if service_path not in sys.path:
        sys.path.insert(0, service_path)
