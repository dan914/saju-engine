"""Unweighted element distribution calculator for testing.

This mirrors the mapping logic used inside ``SajuOrchestrator`` but removes the
stem/branch weighting so that each pillar contributes the same mass. The class
can be used to compare how element ratios change when every stem/branch is
counted equally (1.0 each).
"""

from __future__ import annotations

from typing import Dict

# Element mapping reused from ``saju_orchestrator``
STEM_TO_ELEMENT = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

BRANCH_TO_ELEMENT = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}


class UnweightedElementDistribution:
    """Calculate element ratios without stem/branch weighting.

    Each pillar contributes two counts (stem + branch). The counts are normalised
    to a 0~1 range by dividing with the total contributions so the output shape
    matches the existing ``elements_distribution`` field from the orchestrator.
    """

    _SLOTS = ("year", "month", "day", "hour")

    def calculate(self, pillars: Dict[str, str]) -> Dict[str, float]:
        counts = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
        contributions = 0.0

        for slot in self._SLOTS:
            pillar = pillars.get(slot)
            if not pillar or len(pillar) < 2:
                continue

            stem, branch = pillar[0], pillar[1]

            stem_elem = STEM_TO_ELEMENT.get(stem)
            if stem_elem:
                counts[stem_elem] += 1.0
                contributions += 1.0

            branch_elem = BRANCH_TO_ELEMENT.get(branch)
            if branch_elem:
                counts[branch_elem] += 1.0
                contributions += 1.0

        if contributions:
            counts = {k: v / contributions for k, v in counts.items()}

        return counts


__all__ = ["UnweightedElementDistribution"]
