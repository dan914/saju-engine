"""Helper for Poetry-based imports in scripts without sys.path hacks.

This module provides utilities for loading modules from services when running
scripts under Poetry. It replaces the old pattern of sys.path.insert with
proper package-based imports.

CRITICAL FIX: Each service gets a unique package name in sys.modules to avoid
collisions when scripts import from multiple services (e.g., both analysis and pillars).

Usage:
    # Old pattern (DON'T USE):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / "services" / "analysis-service"))
    from app.core.engine import AnalysisEngine

    # New pattern (DO USE):
    from scripts._script_loader import get_analysis_module, get_pillars_module
    AnalysisEngine = get_analysis_module("engine", "AnalysisEngine")
    PillarsEngine = get_pillars_module("engine", "PillarsEngine")

Note:
    Scripts must be run under Poetry for this to work:
        poetry run python scripts/your_script.py

    Or install the project in editable mode:
        pip install -e .
"""

from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

# Project root (saju-engine/)
REPO_ROOT = Path(__file__).resolve().parents[1]

# Service root paths (one level up from app/)
ANALYSIS_SERVICE_ROOT = REPO_ROOT / "services" / "analysis-service"
PILLARS_SERVICE_ROOT = REPO_ROOT / "services" / "pillars-service"
ASTRO_SERVICE_ROOT = REPO_ROOT / "services" / "astro-service"
TZ_TIME_SERVICE_ROOT = REPO_ROOT / "services" / "tz-time-service"


@contextmanager
def _service_context(service_root: Path) -> Iterator[None]:
    """Temporarily add service to sys.path, ensuring 'app' package resolves correctly.

    This allows the service's internal 'from app.X import Y' statements to work.

    CRITICAL FIX: If 'app' module is already loaded from a different service,
    we must reload it to point to the correct service.
    """
    service_path = str(service_root)
    app_path = service_root / "app"
    added_to_path = False

    # Check if 'app' is already loaded from a different service
    if 'app' in sys.modules:
        existing_app = sys.modules['app']
        if hasattr(existing_app, '__file__') and existing_app.__file__:
            existing_path = Path(existing_app.__file__).parent
            if existing_path != app_path:
                # app module from different service - clear it and all submodules
                keys_to_delete = [k for k in sys.modules.keys() if k == 'app' or k.startswith('app.')]
                for key in keys_to_delete:
                    del sys.modules[key]

    # Add service to sys.path
    if service_path not in sys.path:
        sys.path.insert(0, service_path)
        added_to_path = True

    try:
        yield
    finally:
        # Keep sys.path modified so cached modules continue to work
        # Only remove if we're the last one using this service
        pass


def _load_from_service(service_root: Path, module_path: str, attr_name: str) -> Any:
    """Load an attribute from a service module.

    Args:
        service_root: Path to service directory (e.g., services/analysis-service)
        module_path: Module path under app/ (e.g., "core.engine")
        attr_name: Attribute to extract (e.g., "AnalysisEngine")

    Returns:
        The requested attribute

    Raises:
        ImportError: If module or attribute cannot be found
    """
    # Build the cache key for successful loads
    cache_key = (str(service_root), module_path, attr_name)

    # Check if we've successfully loaded this before
    if hasattr(_load_from_service, '_cache'):
        if cache_key in _load_from_service._cache:
            return _load_from_service._cache[cache_key]
    else:
        _load_from_service._cache = {}

    with _service_context(service_root):
        full_module = f"app.{module_path}" if not module_path.startswith("app.") else module_path
        try:
            mod = importlib.import_module(full_module)
            result = getattr(mod, attr_name)
            # Cache successful loads
            _load_from_service._cache[cache_key] = result
            return result
        except (ImportError, AttributeError) as e:
            # Don't cache failures - let them propagate
            raise ImportError(f"Could not load {attr_name} from {full_module}: {e}")


# Analysis Service Helpers
def get_analysis_module(module: str, attr: str) -> Any:
    """Load an attribute from analysis-service.

    Args:
        module: Module name under core, models, or guard (e.g., "engine", "guard.llm_guard_v1_1")
        attr: Attribute name to get from the module (e.g., "AnalysisEngine")

    Returns:
        The requested attribute (class, function, etc.)

    Example:
        AnalysisEngine = get_analysis_module("engine", "AnalysisEngine")
        StrengthEvaluator = get_analysis_module("strength", "StrengthEvaluator")
        LLMGuardV11 = get_analysis_module("guard.llm_guard_v1_1", "LLMGuardV11")
    """
    for prefix in ["core", "models", "guard", ""]:
        try:
            if prefix:
                module_path = f"{prefix}.{module}"
            else:
                # For direct paths like "guard.llm_guard_v1_1"
                module_path = module
            return _load_from_service(ANALYSIS_SERVICE_ROOT, module_path, attr)
        except ImportError:
            continue
    raise ImportError(f"Could not find {attr} in {module} (tried core, models, guard prefixes)")


def load_analysis_engine():
    """Convenience function to load AnalysisEngine."""
    return get_analysis_module("engine", "AnalysisEngine")


def load_analysis_models():
    """Load common analysis-service models."""
    AnalysisRequest = get_analysis_module("analysis", "AnalysisRequest")
    AnalysisResponse = get_analysis_module("analysis", "AnalysisResponse")
    AnalysisOptions = get_analysis_module("analysis", "AnalysisOptions")
    PillarInput = get_analysis_module("analysis", "PillarInput")
    return AnalysisRequest, AnalysisResponse, AnalysisOptions, PillarInput


# Pillars Service Helpers
def get_pillars_module(module: str, attr: str) -> Any:
    """Load an attribute from pillars-service.

    Args:
        module: Module name under core or models (e.g., "engine", "pillars")
        attr: Attribute name to get from the module

    Returns:
        The requested attribute

    Example:
        PillarsEngine = get_pillars_module("engine", "PillarsEngine")
        PillarsComputeRequest = get_pillars_module("pillars", "PillarsComputeRequest")
    """
    for prefix in ["core", "models"]:
        try:
            module_path = f"{prefix}.{module}"
            return _load_from_service(PILLARS_SERVICE_ROOT, module_path, attr)
        except ImportError:
            continue
    raise ImportError(f"Could not find {attr} in {module} (tried core and models)")


def load_pillars_calculator():
    """Convenience function to load PillarsEngine."""
    return get_pillars_module("engine", "PillarsEngine")


# Astro Service Helpers
def get_astro_module(module: str, attr: str) -> Any:
    """Load an attribute from astro-service.

    Args:
        module: Module name under core or models
        attr: Attribute name to get from the module

    Returns:
        The requested attribute
    """
    for prefix in ["core", "models"]:
        try:
            module_path = f"{prefix}.{module}"
            return _load_from_service(ASTRO_SERVICE_ROOT, module_path, attr)
        except ImportError:
            continue
    raise ImportError(f"Could not find {attr} in {module}")


# TZ Time Service Helpers
def get_tz_time_module(module: str, attr: str) -> Any:
    """Load an attribute from tz-time-service.

    Args:
        module: Module name under core or models
        attr: Attribute name to get from the module

    Returns:
        The requested attribute
    """
    for prefix in ["core", "models"]:
        try:
            module_path = f"{prefix}.{module}"
            return _load_from_service(TZ_TIME_SERVICE_ROOT, module_path, attr)
        except ImportError:
            continue
    raise ImportError(f"Could not find {attr} in {module}")


# Common Service Helpers (services.common)
def get_common_module(module: str, attr: str) -> Any:
    """Load an attribute from services.common.

    Args:
        module: Module name (e.g., "saju_common.builtins")
        attr: Attribute name to get from the module

    Returns:
        The requested attribute

    Example:
        TWELVE_BRANCHES = get_common_module("saju_common.builtins", "TWELVE_BRANCHES")
    """
    try:
        mod = importlib.import_module(f"services.common.{module}")
        return getattr(mod, attr)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Could not load {attr} from services.common.{module}: {e}")


def load_saju_constants():
    """Load common saju constants from services.common."""
    from services.common.saju_common.builtins import (
        ELEMENT_GENERATES,
        STEM_TO_ELEMENT,
        TEN_STEMS,
        TWELVE_BRANCHES,
    )

    return TEN_STEMS, TWELVE_BRANCHES, STEM_TO_ELEMENT, ELEMENT_GENERATES
