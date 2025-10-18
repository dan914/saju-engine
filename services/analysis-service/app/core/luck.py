"""Luck direction and start-age calculations.

This module now imports from saju_common.engines for shared implementations.
All functionality has been moved to the common package for cross-service reuse.
This file is maintained for backward compatibility.
"""

from __future__ import annotations

# Import from common package for shared implementations
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parents[4] / "services" / "common"))

# Import and re-export for backward compatibility
from saju_common.engines import LuckCalculator, LuckContext, ShenshaCatalog

__all__ = ["LuckCalculator", "LuckContext", "ShenshaCatalog"]
