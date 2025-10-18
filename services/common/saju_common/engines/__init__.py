"""Shared analysis engines for saju services.

This package contains core calculation engines extracted from analysis-service
to be shared across multiple services (pillars-service, analysis-service, etc.).

Architecture Decision:
- Code-level sharing via common package (not runtime HTTP calls)
- Pure logic/data/policy engines only (no HTTP/DB access)
- Maintains same function signatures as original implementations
"""

from .luck import LuckCalculator, LuckContext
from .school import SchoolProfileManager
from .shensha import ShenshaCatalog

__all__ = [
    "LuckCalculator",
    "LuckContext",
    "ShenshaCatalog",
    "SchoolProfileManager",
]
