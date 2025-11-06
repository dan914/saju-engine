# -*- coding: utf-8 -*-
"""DeukseEvaluator (得勢 / 득세 / Element Momentum) v1.0

Evaluates strength contribution from five-element distribution balance and climate alignment.
Traditional component representing 35% of total strength in orthodox Saju theory.

Components:
1. Balance score: Penalizes uneven element distribution (variance + skew)
2. Climate adjustment: Bonuses for climate-appropriate elements (寒/熱/燥/濕)

Policy: strength_policy_v2.json > deukse
"""
from __future__ import annotations

from typing import Any, Dict

from saju_common.policy_loader import load_policy_json


class DeukseEvaluator:
    """得勢 (Element Momentum) Evaluator.

    Calculates strength contribution from:
    - Element distribution balance (variance + skew penalties)
    - Climate alignment (bonuses for needed elements)

    Score range: -25 to +35 (before normalization to 35-point scale)
    - Perfect balance (20% each) + good climate: ~+35
    - Severe imbalance + bad climate: ~-25
    """

    def __init__(self):
        """Load deukse policy from strength_policy_v2.json."""
        policy = load_policy_json("strength_policy_v2.json")
        self.config = policy["deukse"]
        self.balance_cfg = self.config["balance"]
        self.climate_cfg = self.config["climate_adjust"]

        # Extract configuration values
        self.target_percent = self.balance_cfg["target_percent"]  # 20.0
        self.var_max = self.balance_cfg["var_max"]  # 1600.0
        self.dispersion_scale = self.balance_cfg["dispersion_penalty"]["scale"]  # -8.0
        self.dispersion_cap = self.balance_cfg["dispersion_penalty"]["cap"]  # -15.0
        self.skew_threshold = self.balance_cfg["skew_penalty"]["threshold"]  # 25.0
        self.skew_scale = self.balance_cfg["skew_penalty"]["scale"]  # -6.0
        self.climate_min = self.climate_cfg["cap"]["min"]  # -10.0
        self.climate_max = self.climate_cfg["cap"]["max"]  # 10.0
        self.climate_vectors = self.climate_cfg["adjust_vectors"]

    def _calculate_variance(self, elements: Dict[str, float]) -> float:
        """Calculate variance of element percentages.

        Variance = sum((x - target)^2) for each element
        Perfect balance (20% each) → variance = 0
        Extreme imbalance (100% one element) → variance = 1600

        Args:
            elements: Element distribution as percentages (sum to 100)

        Returns:
            Variance value (0 to ~1600)
        """
        variance = 0.0
        for elem in ["木", "火", "土", "金", "水"]:
            percent = elements.get(elem, 0.0) * 100  # Convert to percentage
            diff = percent - self.target_percent
            variance += diff**2
        return variance

    def _calculate_max_gap(self, elements: Dict[str, float]) -> float:
        """Calculate maximum gap between any element and target.

        Max gap = max(|percent - 20%|) for all elements
        Perfect balance → gap = 0
        Extreme (e.g., 金:50%, others:12.5%) → gap = 30

        Args:
            elements: Element distribution as percentages (sum to 100)

        Returns:
            Maximum absolute deviation from target (0 to 80)
        """
        max_gap = 0.0
        for elem in ["木", "火", "土", "金", "水"]:
            percent = elements.get(elem, 0.0) * 100
            gap = abs(percent - self.target_percent)
            max_gap = max(max_gap, gap)
        return max_gap

    def _balance_score(self, elements: Dict[str, float]) -> float:
        """Calculate balance score with variance and skew penalties.

        Two penalties:
        1. Dispersion penalty: Based on variance (how uneven overall)
        2. Skew penalty: Based on max gap (if one element dominates/lacks)

        Args:
            elements: Element distribution (sum to 1.0, not percentage)

        Returns:
            Balance score (-21 to 0)
            - Perfect balance: 0
            - Moderate imbalance: -5 to -10
            - Severe imbalance: -15 to -21
        """
        # Calculate variance penalty
        variance = self._calculate_variance(elements)
        dispersion_penalty = (variance / self.var_max) * self.dispersion_scale
        dispersion_penalty = max(dispersion_penalty, self.dispersion_cap)

        # Calculate skew penalty (only if exceeds threshold)
        max_gap = self._calculate_max_gap(elements)
        skew_penalty = 0.0
        if max_gap > self.skew_threshold:
            excess = max_gap - self.skew_threshold
            skew_penalty = excess * self.skew_scale

        total = dispersion_penalty + skew_penalty
        return round(total, 2)

    def _climate_bonus(self, elements: Dict[str, float], climate_segment: str) -> float:
        """Calculate climate adjustment bonus.

        Bonuses for having climate-appropriate elements:
        - 寒 (cold): Need 火 (+3.0) and 土 (+1.5)
        - 熱 (hot): Need 水 (+3.0) and 金 (+1.5)
        - 燥 (dry): Need 水 (+2.0)
        - 濕 (humid): Need 土 (+2.0)

        Bonus is scaled by actual percentage of needed element.

        Args:
            elements: Element distribution (sum to 1.0)
            climate_segment: "寒", "熱", "燥", or "濕"

        Returns:
            Climate bonus (0 to +10.0, capped)
            - Good alignment: +5 to +10
            - Neutral: 0
            - No cap on negative (not implemented in policy)
        """
        if climate_segment not in self.climate_vectors:
            return 0.0

        bonus = 0.0
        needed = self.climate_vectors[climate_segment]

        for elem, boost in needed.items():
            percent = elements.get(elem, 0.0)
            # Scale boost by actual percentage
            # If element at 20% (target), give full boost
            # If element at 10%, give half boost
            # If element at 0%, give no boost
            scaled_boost = boost * (percent / (self.target_percent / 100))
            bonus += scaled_boost

        # Apply cap
        bonus = max(self.climate_min, min(self.climate_max, bonus))
        return round(bonus, 2)

    def evaluate(
        self, elements: Dict[str, float], climate_segment: str | None = None
    ) -> Dict[str, Any]:
        """Evaluate 得勢 (element momentum) score.

        Args:
            elements: Element distribution (木/火/土/金/水 → decimal, sum to 1.0)
            climate_segment: "寒"/"熱"/"燥"/"濕" or None

        Returns:
            {
                "score": float,  # Total deukse score (-25 to +35, raw)
                "balance_score": float,  # Balance component (-21 to 0)
                "climate_bonus": float,  # Climate component (0 to +10)
                "variance": float,  # Element variance (for diagnostics)
                "max_gap": float,  # Maximum element deviation (for diagnostics)
                "climate_segment": str | None
            }
        """
        # Calculate balance score (penalties)
        balance = self._balance_score(elements)

        # Calculate climate bonus
        climate = self._climate_bonus(elements, climate_segment) if climate_segment else 0.0

        # Total deukse score
        total = balance + climate

        # Diagnostics
        variance = self._calculate_variance(elements)
        max_gap = self._calculate_max_gap(elements)

        return {
            "score": round(total, 2),
            "balance_score": balance,
            "climate_bonus": climate,
            "variance": round(variance, 2),
            "max_gap": round(max_gap, 2),
            "climate_segment": climate_segment,
        }
