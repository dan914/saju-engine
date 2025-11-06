
"""Explain, events, and alerts helpers for luck v1.1.2."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional

from .luck_components import RawComputationResult
from .luck_hierarchy import HierarchyResult
from .policy_config import LuckPolicyConfig


def build_explain(
    *,
    raw_result: RawComputationResult,
    hierarchy: HierarchyResult,
    frame_kind: str,
    attribution_notes: Optional[List[str]] = None,
) -> Dict[str, object]:
    components = raw_result.components.as_dict()
    gates = {**hierarchy.gates, "total": hierarchy.gate_total}
    tracks = {
        "state": components.get("sibsin", 0.0) + components.get("unseong12", 0.0) + components.get("season", 0.0),
        "event": components.get("relations", 0.0) + components.get("taese", 0.0),
    }
    frame_contrib = {
        "raw": raw_result.components.total(),
        "normalized": hierarchy.normalized,
        "frame_kind": frame_kind,
    }
    explain = {
        "raw_components": components,
        "gates": gates,
        "tracks": tracks,
        "frame_contrib": frame_contrib,
    }
    if attribution_notes:
        explain["attribution_notes"] = attribution_notes
    return explain


def collect_events(seeds: Mapping[str, object] | None) -> List[str]:
    if not isinstance(seeds, Mapping):
        return []
    events = seeds.get("events")
    if isinstance(events, list):
        return [str(evt) for evt in events]
    return []


def generate_alerts(
    *,
    frame_kind: str,
    normalized_score: float,
    events: List[str],
    policy: LuckPolicyConfig,
) -> Dict[str, object]:
    alerts_cfg = policy.alerts or {}
    alerts: Dict[str, object] = {}

    level1 = alerts_cfg.get("level1_thresholds", {})
    frame_thresholds = level1.get(frame_kind, {})
    if frame_thresholds:
        good_thr = frame_thresholds.get("good")
        caution_thr = frame_thresholds.get("caution")
        if good_thr is not None and normalized_score >= good_thr:
            alerts.setdefault("level1", []).append("good")
        if caution_thr is not None and normalized_score <= caution_thr:
            alerts.setdefault("level1", []).append("caution")

    level2 = alerts_cfg.get("level2_triggers", [])
    for trigger in level2:
        trigger_id = trigger.get("id")
        when = trigger.get("when", {})
        if trigger_id and _event_matches(trigger_id, when, events):
            alerts.setdefault("level2", []).append(trigger_id)

    return alerts


def _event_matches(trigger_id: str, when: Mapping[str, object], events: List[str]) -> bool:
    if trigger_id not in events:
        return False
    for key, expected in when.items():
        if key.endswith("pillar_eq_natal") or key.endswith("pillar_eq_natal_reverse"):
            continue
        if events.count(key) < int(expected is True):
            return False
    return True
