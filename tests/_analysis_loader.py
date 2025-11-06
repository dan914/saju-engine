"""Helpers for importing analysis-service modules without sys.path hacks."""

from __future__ import annotations

import importlib
import sys
import types
from functools import lru_cache
from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parent.parent / "services" / "analysis-service" / "app"


def _ensure_app_package() -> None:
    if "app" not in sys.modules:
        pkg = types.ModuleType("app")
        pkg.__path__ = [str(APP_ROOT)]  # type: ignore[attr-defined]
        sys.modules["app"] = pkg


@lru_cache(maxsize=None)
def load_app_module(module: str):
    """Load an analysis-service module via the ``app`` package."""
    _ensure_app_package()
    qualified = module if module.startswith("app.") else f"app.{module}"
    return importlib.import_module(qualified)


def get_core_attr(module: str, attr: str) -> Any:
    mod = load_app_module(f"app.core.{module}")
    return getattr(mod, attr)


def get_model_attr(module: str, attr: str) -> Any:
    mod = load_app_module(f"app.models.{module}")
    return getattr(mod, attr)
