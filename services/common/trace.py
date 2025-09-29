"""Shared trace metadata helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(slots=True)
class TraceMetadata:
    """Represents common trace fields across services."""

    rule_id: str
    delta_t_seconds: float
    tz: Dict[str, Any]
    astro: Dict[str, Any] | None = None
    boundary_policy: str | None = None
    epsilon_seconds: float | None = None
    flags: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable dict representation."""
        payload: Dict[str, Any] = {
            "rule_id": self.rule_id,
            "deltaTSeconds": self.delta_t_seconds,
            "tz": self.tz,
        }
        if self.astro is not None:
            payload["astro"] = self.astro
        if self.boundary_policy is not None:
            payload["boundaryPolicy"] = self.boundary_policy
        if self.epsilon_seconds is not None:
            payload["epsilonSeconds"] = self.epsilon_seconds
        if self.flags:
            payload["flags"] = self.flags
        return payload
