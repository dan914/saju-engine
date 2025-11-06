# -*- coding: utf-8 -*-
"""Centralized policy file resolution.

This module provides policy file resolution using Pydantic Settings.
Configuration can be provided via:
- Environment variables (SAJU_POLICY_ROOT, SAJU_POLICY_DIRS)
- .env file in repository root
- Programmatic override via settings instance

Usage:
    >>> from saju_common.policy_loader import resolve_policy_path, load_policy_json
    >>> data = load_policy_json("luck_flow_policy_v1.json")

    >>> # Override via environment
    >>> import os
    >>> os.environ['SAJU_POLICY_ROOT'] = '/custom/path'
    >>> from saju_common.settings import SajuSettings
    >>> custom_settings = SajuSettings()
    >>> path = custom_settings.resolve_policy_path("strength_policy_v2.json")
"""
import json
from pathlib import Path


def resolve_policy_path(filename: str) -> Path:
    """Resolve policy file path using global settings.

    Args:
        filename: Policy filename to search for

    Returns:
        Full path to policy file

    Raises:
        FileNotFoundError: If policy file not found

    Example:
        >>> path = resolve_policy_path("strength_policy_v2.json")
        >>> assert path.exists()
    """
    # Import here to avoid circular dependency
    from .settings import settings

    return settings.resolve_policy_path(filename)


def load_policy_json(filename: str):
    path = resolve_policy_path(filename)
    return json.loads(path.read_text(encoding="utf-8"))
