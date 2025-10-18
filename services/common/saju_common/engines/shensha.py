"""Shensha catalog for star/fortune detection.

Extracted from analysis-service to services/common for shared use.
"""

from __future__ import annotations

import json
from typing import Dict

from policy_loader import resolve_policy_path

# Use policy loader for flexible path resolution
SHENSHA_CATALOG_PATH = resolve_policy_path("shensha_catalog_v1.json")


class ShenshaCatalog:
    """Manage shensha (神煞) catalog and enabled stars list."""

    def __init__(self) -> None:
        with SHENSHA_CATALOG_PATH.open("r", encoding="utf-8") as f:
            self._catalog = json.load(f)

    def list_enabled(self, pro_mode: bool = False) -> Dict[str, object]:
        """
        Get list of enabled shensha stars.

        Args:
            pro_mode: If True, use pro_mode configuration

        Returns:
            Dict with keys:
                - enabled: bool (whether catalog is enabled)
                - list: List[str] (list of enabled shensha IDs)
        """
        data = self._catalog.get("pro_mode" if pro_mode else "default", {})
        return {"enabled": data.get("enabled", False), "list": data.get("list", [])}
