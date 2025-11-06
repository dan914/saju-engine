"""Compatibility helpers for alternate presentation layers.

These helpers transform the existing orchestrator payload into a view that more
closely matches external reporting (e.g. equal-weight element ratios, multi-role
Yongshin output) while keeping the underlying engines untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .utils_strength_yongshin import ELEM_TO_KO

# Branch main stem mapping (본기)
_BRANCH_MAIN_TO_ELEM = {
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

_STEM_TO_ELEM = {
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

_ELEMENTS = ("木", "火", "土", "金", "水")

_ELEM_KO = {
    "木": "목",
    "火": "화",
    "土": "토",
    "金": "금",
    "水": "수",
}

# Bridge element candidates for obvious clashes (목-금, 화-금 등)
_BRIDGE_RULES = {
    frozenset({"목", "금"}): "수",
    frozenset({"금", "화"}): "토",
    frozenset({"화", "수"}): "목",
    frozenset({"수", "토"}): "금",
    frozenset({"토", "목"}): "화",
}

_BRANCH_HIDDEN_STEMS = {
    "子": {"main": "癸"},
    "丑": {"main": "己", "mid": "癸", "res": "辛"},
    "寅": {"main": "甲", "mid": "丙", "res": "戊"},
    "卯": {"main": "乙"},
    "辰": {"main": "戊", "mid": "乙", "res": "癸"},
    "巳": {"main": "丙", "mid": "庚", "res": "戊"},
    "午": {"main": "丁", "mid": "己"},
    "未": {"main": "己", "mid": "乙", "res": "丁"},
    "申": {"main": "庚", "mid": "壬", "res": "戊"},
    "酉": {"main": "辛"},
    "戌": {"main": "戊", "mid": "辛", "res": "丁"},
    "亥": {"main": "壬", "mid": "甲"},
}

_HOUR_START_HOUR = {
    "子": 23,
    "丑": 1,
    "寅": 3,
    "卯": 5,
    "辰": 7,
    "巳": 9,
    "午": 11,
    "未": 13,
    "申": 15,
    "酉": 17,
    "戌": 19,
    "亥": 21,
}

_DEFAULT_BUCKET_SEQUENCE = ("mid", "main", "res")
_BRANCH_BUCKET_SEQUENCE = {
    "子": ("main", "main", "main"),
    "丑": _DEFAULT_BUCKET_SEQUENCE,
    "寅": _DEFAULT_BUCKET_SEQUENCE,
    "卯": ("main", "main", "main"),
    "辰": _DEFAULT_BUCKET_SEQUENCE,
    "巳": ("res", "mid", "main"),
    "午": ("mid", "main", "main"),
    "未": _DEFAULT_BUCKET_SEQUENCE,
    "申": _DEFAULT_BUCKET_SEQUENCE,
    "酉": ("main", "main", "main"),
    "戌": _DEFAULT_BUCKET_SEQUENCE,
    "亥": ("mid", "main", "main"),
}

HOUR_ANCHOR_MINUTES = 0


def _parse_birth_dt(value: Optional[object]) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            if value.endswith("Z"):
                value = value.replace("Z", "+00:00")
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def resolve_branch_stem(branch: str, slot: str, birth_dt: Optional[datetime]) -> Optional[str]:
    hidden = _BRANCH_HIDDEN_STEMS.get(branch)
    if not hidden:
        return None

    if slot != "hour" or birth_dt is None:
        return hidden.get("main")

    start_hour = _HOUR_START_HOUR.get(branch)
    if start_hour is None:
        return hidden.get("main")

    start_dt = birth_dt.replace(hour=start_hour, minute=HOUR_ANCHOR_MINUTES, second=0, microsecond=0)
    if start_hour == 23 and birth_dt.hour < 23:
        start_dt -= timedelta(days=1)
    if birth_dt < start_dt:
        start_dt -= timedelta(hours=2)

    offset_minutes = (birth_dt - start_dt).total_seconds() / 60.0
    offset_minutes = max(0.0, offset_minutes % 120.0)

    if offset_minutes < 40.0:
        bucket_index = 0
    elif offset_minutes < 80.0:
        bucket_index = 1
    else:
        bucket_index = 2

    sequence = _BRANCH_BUCKET_SEQUENCE.get(branch, _DEFAULT_BUCKET_SEQUENCE)
    if len(sequence) < 3:
        sequence = sequence + (sequence[-1],) * (3 - len(sequence))

    slot = sequence[min(bucket_index, len(sequence) - 1)]
    stem = hidden.get(slot)
    if stem:
        return stem

    for key in ("main", "mid", "res"):
        stem = hidden.get(key)
        if stem:
            return stem
    return None


@dataclass
class YongshinItem:
    element: str
    roles: set[str] = field(default_factory=set)
    score: float = 0.0
    why: Optional[str] = None

    def merge(self, role: Optional[str], score: Optional[float] = None) -> None:
        if role:
            self.roles.add(role)
        if score is not None:
            self.score = max(self.score, score)

    @property
    def level(self) -> str:
        if self.score >= 0.65:
            return "High"
        if self.score >= 0.4:
            return "Medium"
        return "Low"

    def as_payload(self) -> Dict[str, object]:
        rationale = self.why or ", ".join(sorted(self.roles)) or ""
        return {
            "element": self.element,
            "roles": sorted(self.roles),
            "level": self.level,
            "score": round(self.score, 3),
            "why": rationale,
        }


def _element_to_korean(elem: str) -> str:
    if elem in _ELEM_KO:
        return _ELEM_KO[elem]
    if elem in ELEM_TO_KO:
        return ELEM_TO_KO[elem]
    return elem


def to_equal_slot_elements(
    pillars: Dict[str, str],
    birth_dt_value: Optional[object] = None,
) -> Dict[str, float]:
    """Map four pillars to 8 equally weighted slots (stems + branch-main).

    Each stem/branch contributes a weight of 1.0, so the final percentage is
    always a multiple of 12.5 (8 slots).
    """

    birth_dt = _parse_birth_dt(birth_dt_value)
    counts = {elem: 0.0 for elem in _ELEMENTS}
    for slot, pillar in pillars.items():
        if not pillar or len(pillar) < 2:
            continue
        stem, branch = pillar[0], pillar[1]
        stem_elem = _STEM_TO_ELEM.get(stem)
        if stem_elem:
            counts[stem_elem] += 1.0
        branch_stem = resolve_branch_stem(branch, slot, birth_dt)
        branch_elem = _STEM_TO_ELEM.get(branch_stem) if branch_stem else None
        if not branch_elem:
            branch_elem = _BRANCH_MAIN_TO_ELEM.get(branch)
        if branch_elem:
            counts[branch_elem] += 1.0

    total_slots = sum(counts.values()) or 1.0
    return {elem: round((value / total_slots) * 100.0, 1) for elem, value in counts.items()}


def annotate_elements(dist: Dict[str, float]) -> Dict[str, Dict[str, object]]:
    """Attach qualitative labels to element ratios."""

    def label(value: float) -> str:
        if value <= 0.0:
            return "부족"
        if value <= 12.5:
            return "적정"
        if value <= 25.0:
            return "발달"
        return "과다"

    return {elem: {"pct": dist.get(elem, 0.0), "label": label(dist.get(elem, 0.0))} for elem in _ELEMENTS}


def strength_label_view(strength: Dict[str, object]) -> Dict[str, object]:
    """Build the 5-step strength view using existing grade/bin information."""

    label = strength.get("grade_code") or _map_bin_to_grade(strength.get("bin"))
    score_norm = strength.get("score_normalized")
    score = strength.get("score")
    boundary = False
    if isinstance(score_norm, (float, int)):
        boundary = min(abs(score_norm - 0.4), abs(score_norm - 0.6)) < 0.02
    return {
        "label": label,
        "bin": strength.get("bin"),
        "score_normalized": score_norm,
        "score": score,
        "boundary": boundary,
    }


def _map_bin_to_grade(bin_value: Optional[str]) -> str:
    mapping = {
        "very_weak": "극신약",
        "weak": "신약",
        "balanced": "중화",
        "strong": "신강",
        "very_strong": "극신강",
    }
    return mapping.get(bin_value, "중화")


def _ensure_item(items: Dict[str, YongshinItem], element: str) -> YongshinItem:
    elem = _element_to_korean(element)
    if elem not in items:
        items[elem] = YongshinItem(element=elem)
    return items[elem]


def _gather_over_elements(annotated: Dict[str, Dict[str, object]]) -> List[str]:
    return [elem for elem, info in annotated.items() if info.get("label") == "과다"]


def build_yongshin_view(
    yongshin: Dict[str, object],
    annotated_elements: Dict[str, Dict[str, object]],
    season: str,
    strength_label: Optional[str],
) -> Dict[str, object]:
    """Aggregate Yongshin information into a multi-role payload."""

    items: Dict[str, YongshinItem] = {}
    integrated = yongshin.get("integrated") if isinstance(yongshin, dict) else None
    split = yongshin.get("split") if isinstance(yongshin, dict) else None

    # Base scores from integrated view (if available)
    if isinstance(integrated, dict):
        scores = integrated.get("scores", {})
        for elem_en, score in scores.items():
            item = _ensure_item(items, elem_en)
            item.merge(role=None, score=score)
        primary = integrated.get("primary", {})
        primary_elem = primary.get("elem_ko") or primary.get("elem")
    else:
        primary = {}
        primary_elem = None

    # Roles from split view (억부/조후 등)
    if isinstance(split, dict):
        climate_primary = split.get("climate", {}).get("primary")
        if climate_primary:
            _ensure_item(items, climate_primary).merge("조후")
        eokbu = split.get("eokbu", {})
        for key in ("primary", "secondary"):
            elem = eokbu.get(key)
            if elem:
                _ensure_item(items, elem).merge("억부")

    # Fallback when integrated missing: use legacy list
    if not items and isinstance(yongshin, dict):
        legacy = yongshin.get("yongshin") or []
        if legacy:
            item = _ensure_item(items, legacy[0])
            item.merge("억부")
            primary_elem = legacy[0]

    # Simple 통관 heuristic: clash pairs both 과다
    over = _gather_over_elements(annotated_elements)
    if len(over) >= 2:
        pair = frozenset(over[:2])
        bridge = _BRIDGE_RULES.get(pair)
        if bridge:
            _ensure_item(items, bridge).merge("통관")

    # 종 조건: 극단 강약 & 단일 오행 점유 높음
    annotations = annotated_elements
    for elem, info in annotations.items():
        if info.get("pct", 0.0) >= 62.5:
            for label in ("극신약", "극신강"):
                if strength_label == label:
                    _ensure_item(items, elem).merge("종")

    # Compose result list
    ranked = sorted(
        items.values(),
        key=lambda item: (-item.score, item.element)
    )

    payload_items = [item.as_payload() for item in ranked]
    primary_payload = payload_items[0] if payload_items else None

    return {
        "primary": primary_payload,
        "items": payload_items,
        "confidence": integrated.get("confidence") if isinstance(integrated, dict) else yongshin.get("confidence"),
        "season": season,
    }


def build_compat_view(
    pillars: Dict[str, str],
    strength: Dict[str, object],
    yongshin: Dict[str, object],
    season: str,
    birth_dt: Optional[object] = None,
) -> Dict[str, object]:
    """Assemble the compatibility layer payload."""

    elements = to_equal_slot_elements(pillars, birth_dt)
    annotated = annotate_elements(elements)
    strength_view = strength_label_view(strength)
    yongshin_view = build_yongshin_view(
        yongshin,
        annotated,
        season,
        strength_view["label"],
    )

    return {
        "strength": strength_view,
        "five_elements": annotated,
        "yongshin": yongshin_view,
    }


__all__ = [
    "build_compat_view",
    "to_equal_slot_elements",
    "annotate_elements",
    "resolve_branch_stem",
]
