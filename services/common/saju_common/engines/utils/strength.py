"""Strength profile helper functions for luck engines."""

from __future__ import annotations

from typing import Mapping

from ...seasons import ELEMENT_CONTROLS, ELEMENT_GENERATES, STEM_TO_ELEMENT

_KO_TO_EN = {
    "목": "wood",
    "화": "fire",
    "토": "earth",
    "금": "metal",
    "수": "water",
}

_EN_TO_KO = {v: k for k, v in _KO_TO_EN.items()}


def _normalise_element_key(key: str) -> str:
    key_lower = key.lower()
    if key in _KO_TO_EN:
        return _KO_TO_EN[key]
    if key_lower in _EN_TO_KO:
        return key_lower
    return key_lower


def _as_ko_element(key: str) -> str:
    if key in _KO_TO_EN:
        return key
    return _EN_TO_KO.get(key.lower(), key)


def determine_strength_profile(
    day_master: str,
    element_balance: Mapping[str, float],
    *,
    threshold: float = 0.1,
) -> "Literal['strong','neutral','weak']":
    """Derive a coarse strength profile (신강/중간/신약).

    The calculation follows the expert guideline:
    - Support = 본기(일간 동일 오행) + 생조 오행
    - Control = 극하는 오행
    - Normalise by total sum to keep the score in [-1, +1]
    """

    if not day_master:
        return "neutral"

    dm_element = STEM_TO_ELEMENT.get(day_master)
    if not dm_element:
        return "neutral"

    # Prepare balance map in English keys
    normalised = { _normalise_element_key(k): float(v) for k, v in element_balance.items() }
    total = sum(normalised.values()) or 1.0

    ko_primary = dm_element
    primary = _normalise_element_key(ko_primary)
    produces = _normalise_element_key(ELEMENT_GENERATES[ko_primary])
    controls = _normalise_element_key(ELEMENT_CONTROLS[ko_primary])

    support = normalised.get(primary, 0.0) + normalised.get(produces, 0.0)
    control = normalised.get(controls, 0.0)

    score = (support - control) / total
    if score >= threshold:
        return "strong"
    if score <= -threshold:
        return "weak"
    return "neutral"
