"""Utility helpers for luck engine calculations.

Modules in this package will host shared functions such as 60갑자
transformations, interaction detectors, and scoring glue code. They are
being introduced ahead of the full implementation so other modules can
begin importing from a stable namespace.
"""
from .jiazi import next_pillar, pillar_to_index, index_to_pillar
from .scoring import clamp_score
from .strength import determine_strength_profile
from .categories import compute_categories, apply_geokguk, build_recommendations, CategoryScores

__all__ = [
    "next_pillar",
    "pillar_to_index",
    "index_to_pillar",
    "clamp_score",
    "determine_strength_profile",
    "compute_categories",
    "apply_geokguk",
    "build_recommendations",
    "CategoryScores",
]
