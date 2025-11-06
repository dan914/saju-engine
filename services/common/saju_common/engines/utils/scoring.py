"""Scoring helpers shared across luck engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


def clamp_score(value: float, minimum: float, maximum: float) -> float:
    """Clamp *value* between *minimum* and *maximum*."""

    return max(minimum, min(value, maximum))


@dataclass(slots=True)
class AggregationConfig:
    """Configuration parameters extracted from policy aggregation block."""

    alpha_year_to_month: float = 0.3
    beta_month_to_day: float = 0.2
    day_score_cap: float = 12.0


@dataclass(slots=True)
class ScoringEngine:
    """Utility class that applies aggregation rules from policy JSON."""

    aggregation: AggregationConfig

    @classmethod
    def from_policy(cls, policy: Dict[str, object]) -> "ScoringEngine":
        aggregation = policy.get("aggregation", {}) if policy else {}
        return cls(
            AggregationConfig(
                alpha_year_to_month=float(aggregation.get("alpha_year_to_month", 0.3)),
                beta_month_to_day=float(aggregation.get("beta_month_to_day", 0.2)),
                day_score_cap=float(aggregation.get("day_score_cap", 12.0)),
            )
        )

    def mix_month_score(self, year_score: float, month_score: float) -> float:
        """Combine year and month scores applying alpha/clamp rules."""

        raw = year_score * self.aggregation.alpha_year_to_month + month_score
        return clamp_score(raw, -self.aggregation.day_score_cap, self.aggregation.day_score_cap)

    def mix_day_score(self, month_score: float, day_score: float) -> float:
        """Combine month and day scores applying beta/clamp rules."""

        raw = month_score * self.aggregation.beta_month_to_day + day_score
        return clamp_score(raw, -self.aggregation.day_score_cap, self.aggregation.day_score_cap)
