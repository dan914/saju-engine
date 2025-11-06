"""Luck direction and start-age calculations.

This module now imports from saju_common.engines for shared implementations.
All functionality has been moved to the common package for cross-service reuse.
This file is maintained for backward compatibility.
"""

from __future__ import annotations

# Import and re-export for backward compatibility
from saju_common.engines import (
    LuckCalculator,
    LuckContext,
    ShenshaCatalog,
)

__all__ = ["LuckCalculator", "LuckContext", "ShenshaCatalog"]
