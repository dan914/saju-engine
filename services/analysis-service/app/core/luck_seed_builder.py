"""Helpers for bridging orchestrator outputs to luck engine v1.1.2 seeds."""

from __future__ import annotations

import csv
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from saju_common.policy_loader import load_policy_json

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEN_GOD_ZH_TO_KEY = {
    "比肩": "bi",
    "劫財": "jeok",
    "食神": "sik",
    "傷官": "sang",
    "偏財": "pyeonjae",
    "正財": "jeongjae",
    "七殺": "pyeongwan",
    "偏官": "pyeongwan",
    "正官": "jeonggwan",
    "偏印": "pyeonin",
    "正印": "jeongin",
}

RELATION_KIND_MAP = {
    "chong": "chung",
    "xing": "hyeong",
    "hai": "hae",
    "pa": "pa",
    "sanhe": "hap",
    "banhe": "hap",
    "liuhe": "hap",
    "ganhe": "hap",
    "stemhe": "hap",
    "yuanjin": "hae",
}

RELATION_BONUS_MAP = {
    "sanhe": ["sam_hap_complete"],
    "banhe": ["bang_hap_complete"],
    "liuhe": ["bang_hap_complete"],
    "ganhe": ["stem_hap"],
    "stemhe": ["stem_hap"],
}

CARDINAL_PAIRS = {
    frozenset(("子", "午")),
    frozenset(("卯", "酉")),
}

BRANCH_TO_POLICY_KEY = {
    "子": "zi",
    "丑": "chou",
    "寅": "yin",
    "卯": "mao",
    "辰": "chen",
    "巳": "si",
    "午": "wu",
    "未": "wei",
    "申": "shen",
    "酉": "you",
    "戌": "xu",
    "亥": "hai",
}

STEM_TO_ELEMENT_EN = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}

# 60갑자 cycle helpers (replicated from pillars-service constants)
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SEXAGENARY = [HEAVENLY_STEMS[i % 10] + EARTHLY_BRANCHES[i % 12] for i in range(60)]

YEAR_ANCHOR = (1984, "甲子")  # 1984 JiaZi year anchor
DAY_ANCHOR = (1900, 1, 1, "甲戌")  # 1900-01-01 = 甲戌 anchor

YEAR_STEM_TO_MONTH_START = {
    "甲": "丙",
    "己": "丙",
    "乙": "戊",
    "庚": "戊",
    "丙": "庚",
    "辛": "庚",
    "丁": "壬",
    "壬": "壬",
    "戊": "甲",
    "癸": "甲",
}

# Major solar terms delimiting months
MAJOR_TERMS = [
    "立春",
    "驚蟄",
    "清明",
    "立夏",
    "芒種",
    "小暑",
    "立秋",
    "白露",
    "寒露",
    "立冬",
    "大雪",
    "小寒",
]

TERM_TO_BRANCH = {
    "立春": "寅",
    "驚蟄": "卯",
    "清明": "辰",
    "立夏": "巳",
    "芒種": "午",
    "小暑": "未",
    "立秋": "申",
    "白露": "酉",
    "寒露": "戌",
    "立冬": "亥",
    "大雪": "子",
    "小寒": "丑",
}

# Branch relation lookup (loaded lazily)
_BRANCH_RELATION_INDEX: Dict[frozenset[str], str] | None = None


def _load_branch_relation_index() -> Dict[frozenset[str], str]:
    """Load mapping of branch pairs to relation kinds from policy."""

    global _BRANCH_RELATION_INDEX
    if _BRANCH_RELATION_INDEX is not None:
        return _BRANCH_RELATION_INDEX

    relation_map: Dict[frozenset[str], str] = {}

    try:
        data = load_policy_json("relation_policy.json")
    except FileNotFoundError:
        _BRANCH_RELATION_INDEX = relation_map
        return relation_map
    except Exception:
        _BRANCH_RELATION_INDEX = relation_map
        return relation_map

    relationships = data.get("relationships", {})
    key_to_kind = {
        "沖": "chung",
        "破": "pa",
        "害": "hae",
        "六合": "hap",
        "半合": "hap",
        "刑_三刑": "hyeong",
        "刑_自刑": "hyeong",
        "刑_偏刑": "hyeong",
    }

    for policy_key, kind in key_to_kind.items():
        payload = relationships.get(policy_key)
        if not isinstance(payload, Mapping):
            continue
        rules = payload.get("rules", [])
        if not isinstance(rules, list):
            continue
        for rule in rules:
            branches = rule.get("branches") if isinstance(rule, Mapping) else None
            if not isinstance(branches, list) or len(branches) != 2:
                continue
            relation_map[frozenset(branches)] = kind

    _BRANCH_RELATION_INDEX = relation_map
    return relation_map

ELEMENT_CN_TO_EN = {
    "木": "wood",
    "火": "fire",
    "土": "earth",
    "金": "metal",
    "水": "water",
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class SibsinBreakdown:
    """Aggregated ten-god exposures including hidden tiers."""

    totals: Dict[str, float]
    hidden: Dict[str, Dict[str, float]]
    per_pillar: Dict[str, Dict[str, float]]


@dataclass
class RelationEvent:
    """Normalized relation entry suitable for luck seeds."""

    kind: str
    magnitude: float
    participants: Sequence[str]
    bonus_keys: Sequence[str]
    confidence: Optional[float] = None
    formed: Optional[bool] = None
    original_type: Optional[str] = None


@dataclass
class AxisPattern:
    """Detected axis-pattern events (사정충, 삼형 등)."""

    pattern: str
    state: str  # "complete" | "partial"
    emit_flag: bool = True


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def compute_strength_scalar(strength: Mapping[str, float]) -> float:
    """Map strength normalization (0~100) to the [-1, 1] scalar used by v1.1.2."""

    score = float(strength.get("score_normalized", 50.0))
    scalar = (score - 50.0) / 50.0
    return max(-1.0, min(1.0, scalar))


class LuckSeedBuilder:
    """Convert orchestrator outputs into v1.1.2-compatible seed structures."""

    def __init__(self, ten_gods_calculator):
        from app.core.ten_gods import TenGodsCalculator  # Local import to avoid cycles

        if not isinstance(ten_gods_calculator, TenGodsCalculator):
            raise TypeError("ten_gods_calculator must be a TenGodsCalculator instance")

        self._ten_gods = ten_gods_calculator
        self._hidden_policy = ten_gods_calculator.policy.get("branches_hidden", {})
        self._hidden_roles = build_hidden_role_index(self._hidden_policy)
        self._mapping_rules = ten_gods_calculator._mapping
        self._sheng = ten_gods_calculator._sheng
        self._ke = ten_gods_calculator._ke
        self._ten_gods_label_map = ten_gods_calculator._ten_gods_label_map_zh

        # Transit helpers
        self._solar_term_cache: Dict[int, List[dict]] = {}
        self._data_dir = Path(__file__).resolve().parents[4] / "data"

    # ------------------------------------------------------------------
    # Ten-gods breakdown
    # ------------------------------------------------------------------

    def aggregate_tengod_breakdown(self, ten_gods: Mapping[str, object]) -> SibsinBreakdown:
        totals: Counter[str] = Counter()
        hidden_totals: Dict[str, Counter[str]] = {
            "main": Counter(),
            "middle": Counter(),
            "minor": Counter(),
        }
        per_pillar: Dict[str, Dict[str, float]] = {}

        per_slot = ten_gods.get("by_pillar", {}) if isinstance(ten_gods, Mapping) else {}
        for slot, data in per_slot.items():
            slot_counts: Counter[str] = Counter()
            if not isinstance(data, Mapping):
                continue
            stem_label = data.get("vs_day")
            key = TEN_GOD_ZH_TO_KEY.get(stem_label)
            if key:
                totals[key] += 1.0
                slot_counts[key] += 1.0

            branch = data.get("branch")
            hidden_map = data.get("hidden", {}) if isinstance(data.get("hidden"), Mapping) else {}
            for stem, hidden_label in hidden_map.items():
                tg_key = TEN_GOD_ZH_TO_KEY.get(hidden_label)
                if not tg_key:
                    continue
                role = self._resolve_hidden_role(branch, stem)
                hidden_totals[role][tg_key] += 1.0
                slot_counts[tg_key] += 1.0

            if slot_counts:
                per_pillar[slot] = dict(slot_counts)

        hidden_serialized = {tier: dict(values) for tier, values in hidden_totals.items() if values}
        return SibsinBreakdown(totals=dict(totals), hidden=hidden_serialized, per_pillar=per_pillar)

    def build_transit_breakdown(self, day_stem: str, pillar: str) -> SibsinBreakdown:
        totals: Counter[str] = Counter()
        hidden_totals: Dict[str, Counter[str]] = {
            "main": Counter(),
            "middle": Counter(),
            "minor": Counter(),
        }

        stem = pillar[0]
        branch = pillar[1]

        label = self._rel_label(day_stem, stem)
        key = TEN_GOD_ZH_TO_KEY.get(label)
        if key:
            totals[key] += 1.0

        for hidden_entry in self._hidden_policy.get(branch, []):
            hidden_stem = hidden_entry.get("stem")
            if not hidden_stem:
                continue
            hidden_label = self._rel_label(day_stem, hidden_stem)
            hidden_key = TEN_GOD_ZH_TO_KEY.get(hidden_label)
            if not hidden_key:
                continue
            tier = self._tier_for_role(str(hidden_entry.get("role", "secondary")))
            hidden_totals[tier][hidden_key] += 1.0
            totals[hidden_key] += 1.0

        per_pillar = {"transit": dict(totals)} if totals else {}
        hidden = {tier: dict(values) for tier, values in hidden_totals.items() if values}
        return SibsinBreakdown(totals=dict(totals), hidden=hidden, per_pillar=per_pillar)

    def build_taise_events(
        self,
        *,
        taese_branch: Optional[str],
        frame_branch: Optional[str],
        frame_level: str,
        strength_profile: Optional[str] = None,
        day_branch: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        if not taese_branch or not frame_branch:
            return []

        relation_index = _load_branch_relation_index()
        relation = relation_index.get(frozenset((taese_branch, frame_branch)))
        if not relation:
            if taese_branch == frame_branch:
                relation = "hap"
            else:
                return []

        magnitude = 1.0
        if strength_profile == "weak" and relation in {"hap"}:
            magnitude = 0.5

        event: Dict[str, object] = {
            "relation": relation,
            "magnitude": magnitude,
        }

        if relation == "chung":
            if frame_level == "day":
                event["synergy"] = "synergy_taise_plus_day_branch_chung"
            else:
                event["synergy"] = "synergy_taise_plus_other_branch_chung"

        if day_branch:
            event["day_branch"] = day_branch

        return [event]

    # ------------------------------------------------------------------
    # Derived seed helpers
    # ------------------------------------------------------------------

    def build_frame_seed(
        self,
        breakdown: SibsinBreakdown,
        relation_events: Sequence[RelationEvent],
        axis_patterns: Sequence[AxisPattern],
        *,
        season_branch: Optional[str],
        day_element: Optional[str],
        taese_events: Optional[Sequence[Mapping[str, object]]] = None,
        gates: Optional[Mapping[str, float]] = None,
        unseong_stage: Optional[str] = None,
        transform_effects: Optional[Sequence[Mapping[str, object]]] = None,
        pilar_overlap: Optional[Sequence[Mapping[str, object]]] = None,
    ) -> Dict[str, object]:
        sibsin_payload: Dict[str, object] = {
            "ten_gods": dict(breakdown.totals),
        }
        if breakdown.hidden:
            sibsin_payload["hidden"] = deepcopy(breakdown.hidden)
        if breakdown.per_pillar:
            sibsin_payload["per_pillar"] = deepcopy(breakdown.per_pillar)

        relations_payload: List[Dict[str, object]] = []
        for event in relation_events:
            entry: Dict[str, object] = {
                "kind": event.kind,
                "magnitude": event.magnitude,
                "bonus_keys": list(event.bonus_keys),
                "participants": list(event.participants),
            }
            if event.confidence is not None:
                entry["confidence"] = event.confidence
            if event.formed is not None:
                entry["formed"] = event.formed
            relations_payload.append(entry)

        axis_payload = [
            {
                "pattern": pattern.pattern,
                "state": pattern.state,
                "emit_flag": pattern.emit_flag,
            }
            for pattern in axis_patterns
        ]

        transform_payload: List[Dict[str, object]] = []
        for effect in transform_effects or []:
            if isinstance(effect, Mapping):
                transform_payload.append(dict(effect))

        seed: Dict[str, object] = {
            "sibsin": sibsin_payload,
            "relations": relations_payload,
            "axis_patterns": axis_payload,
            "pilar_overlap": [dict(entry) for entry in (pilar_overlap or []) if isinstance(entry, Mapping)],
            "taese": [dict(entry) for entry in (taese_events or []) if isinstance(entry, Mapping)],
            "season": {
                "branch": season_branch,
                "element": day_element,
            },
            "gates": dict(gates or {}),
            "transform_effects": transform_payload,
        }

        if unseong_stage:
            seed["unseong_stage"] = unseong_stage
            seed["unseong12"] = {unseong_stage: 1.0}

        if relation_events:
            labels: List[str] = []
            for event in relation_events:
                if event.original_type:
                    labels.append(event.original_type)
                elif event.kind:
                    labels.append(event.kind)
            if labels:
                seed["events"] = labels

        return seed

    def element_balance_from_raw(self, elements: Mapping[str, float]) -> Dict[str, float]:
        balance: Dict[str, float] = {}
        for key, value in (elements or {}).items():
            element_key = ELEMENT_CN_TO_EN.get(key, key)
            balance[element_key] = float(value)
        return balance

    def hidden_stems_map(self, ten_gods: Mapping[str, object]) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {}
        per_slot = ten_gods.get("by_pillar", {}) if isinstance(ten_gods, Mapping) else {}
        for slot, data in per_slot.items():
            hidden_map = data.get("hidden") if isinstance(data, Mapping) else None
            if isinstance(hidden_map, Mapping):
                mapping[slot] = [stem for stem in hidden_map.keys()]
        return mapping

    @staticmethod
    def branch_to_policy_key(branch: Optional[str]) -> Optional[str]:
        if not branch:
            return None
        return BRANCH_TO_POLICY_KEY.get(branch, branch.lower())

    @staticmethod
    def stem_to_element_key(stem: Optional[str]) -> Optional[str]:
        if not stem:
            return None
        return STEM_TO_ELEMENT_EN.get(stem)

    def _resolve_hidden_role(self, branch: Optional[str], stem: str) -> str:
        if branch and branch in self._hidden_roles:
            role = self._hidden_roles[branch].get(stem)
            if role:
                return self._tier_for_role(role)
        return "middle"

    def _rel_label(self, day_stem: str, target_stem: str) -> Optional[str]:
        """Delegate to TenGodsCalculator for relation label."""

        if not day_stem or not target_stem:
            return None
        try:
            return self._ten_gods._rel_label(day_stem, target_stem)
        except Exception:
            return None

    @staticmethod
    def _tier_for_role(role: str) -> str:
        mapping = {
            "primary": "main",
            "secondary": "middle",
            "tertiary": "minor",
            "main": "main",
            "middle": "middle",
            "minor": "minor",
        }
        return mapping.get(role, "middle")

    # ------------------------------------------------------------------
    # Transit helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _year_pillar(year: int) -> str:
        anchor_year, anchor_pillar = YEAR_ANCHOR
        anchor_index = SEXAGENARY.index(anchor_pillar)
        offset = year - anchor_year
        return SEXAGENARY[(anchor_index + offset) % 60]

    @staticmethod
    def _month_pillar(year_stem: str, month_branch: str) -> str:
        start_stem = YEAR_STEM_TO_MONTH_START[year_stem]
        start_index = HEAVENLY_STEMS.index(start_stem)
        anchor_index = EARTHLY_BRANCHES.index("寅")
        month_index = EARTHLY_BRANCHES.index(month_branch)
        offset = (month_index - anchor_index) % 12
        stem_index = (start_index + offset) % 10
        return HEAVENLY_STEMS[stem_index] + month_branch

    @staticmethod
    def _day_pillar(local_dt: datetime) -> str:
        anchor_year, anchor_month, anchor_day, anchor_pillar = DAY_ANCHOR
        anchor_index = SEXAGENARY.index(anchor_pillar)
        anchor_dt = datetime(anchor_year, anchor_month, anchor_day, tzinfo=local_dt.tzinfo)
        delta_days = (local_dt.date() - anchor_dt.date()).days
        return SEXAGENARY[(anchor_index + delta_days) % 60]

    def _load_solar_terms(self, year: int) -> List[dict]:
        cached = self._solar_term_cache.get(year)
        if cached is not None:
            return cached

        file_path = self._data_dir / f"terms_{year}.csv"
        entries: List[dict] = []
        if file_path.exists():
            with file_path.open(encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    term = row.get("term")
                    utc_raw = row.get("utc_time")
                    if not term or not utc_raw:
                        continue
                    utc_dt = datetime.fromisoformat(utc_raw.replace("Z", "+00:00"))
                    entries.append(
                        {
                            "term": term,
                            "utc_time": utc_dt,
                        }
                    )
        self._solar_term_cache[year] = entries
        return entries

    def _resolve_month_branch(self, local_dt: datetime, tz: ZoneInfo) -> str:
        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
        year = utc_dt.year
        terms = self._load_solar_terms(year)
        if not terms:
            # fallback to previous year data
            terms = self._load_solar_terms(year - 1)
            if not terms:
                return "寅"  # default to start of spring

        # Ensure we have preceding term even if current before first entry
        if utc_dt < terms[0]["utc_time"]:
            prev_year_terms = self._load_solar_terms(year - 1)
            terms = prev_year_terms + terms

        major_terms = [entry for entry in terms if entry["term"] in MAJOR_TERMS]
        major_terms.sort(key=lambda entry: entry["utc_time"])

        current = major_terms[0]
        for entry in major_terms:
            if entry["utc_time"] <= utc_dt:
                current = entry
            else:
                break
        return TERM_TO_BRANCH.get(current["term"], "寅")

    def compute_transit_pillars(
        self,
        *,
        birth_context: Mapping[str, Any],
        reference_dt: Optional[datetime] = None,
    ) -> Dict[str, Dict[str, str]]:
        tz_name = str(birth_context.get("timezone", "Asia/Seoul"))
        tz = ZoneInfo(tz_name)
        now_local = reference_dt.astimezone(tz) if reference_dt else datetime.now(tz)

        year_pillar = self._year_pillar(now_local.year)
        month_branch = self._resolve_month_branch(now_local, tz)
        month_pillar = self._month_pillar(year_pillar[0], month_branch)
        day_pillar = self._day_pillar(now_local)

        return {
            "year": {"pillar": year_pillar, "stem": year_pillar[0], "branch": year_pillar[1]},
            "month": {"pillar": month_pillar, "stem": month_pillar[0], "branch": month_branch},
            "day": {"pillar": day_pillar, "stem": day_pillar[0], "branch": day_pillar[1]},
            "meta": {
                "timezone": tz_name,
                "timestamp": now_local.isoformat(),
            },
        }

    # ------------------------------------------------------------------
    # Relations and axis patterns
    # ------------------------------------------------------------------

    def build_relation_events(
        self,
        pairs: Sequence[Mapping[str, object]],
        relation_notes: Sequence[str],
    ) -> Tuple[List[RelationEvent], List[AxisPattern]]:
        events: List[RelationEvent] = []

        for entry in pairs or []:
            if not isinstance(entry, Mapping):
                continue
            original_type = str(entry.get("type", "")).lower()
            kind = RELATION_KIND_MAP.get(original_type)
            if not kind:
                continue
            magnitude = float(entry.get("impact_weight", 1.0) or 0.0)
            participants = tuple(entry.get("participants", []))
            bonus_keys = list(RELATION_BONUS_MAP.get(original_type, ()))
            confidence = entry.get("confidence")
            formed = entry.get("formed")
            events.append(
                RelationEvent(
                    kind=kind,
                    magnitude=magnitude if magnitude else 0.0,
                    participants=participants,
                    bonus_keys=tuple(bonus_keys),
                    confidence=float(confidence) if confidence is not None else None,
                    formed=bool(formed) if formed is not None else None,
                    original_type=original_type,
                )
            )

        for note in relation_notes or []:
            if not note or ":" not in note:
                continue
            rel_type, payload = note.split(":", 1)
            rel_type = rel_type.strip().lower()
            kind = RELATION_KIND_MAP.get(rel_type)
            if not kind:
                continue
            participants = tuple(payload.split("/")) if "/" in payload else (payload,)
            events.append(
                RelationEvent(
                    kind=kind,
                    magnitude=1.0,
                    participants=participants,
                    bonus_keys=tuple(RELATION_BONUS_MAP.get(rel_type, ())),
                    original_type=rel_type,
                )
            )

        axis_patterns = self._detect_axis_patterns(events)
        return events, axis_patterns

    def _detect_axis_patterns(self, events: Iterable[RelationEvent]) -> List[AxisPattern]:
        axis_hits = {pair: False for pair in CARDINAL_PAIRS}
        sam_hyeong_complete = False
        sam_hyeong_partial = False

        for event in events:
            if event.kind == "chung" and len(event.participants) == 2:
                pair = frozenset(event.participants)
                if pair in axis_hits:
                    axis_hits[pair] = True

            if event.original_type == "xing":
                if event.formed and len(event.participants) >= 3:
                    sam_hyeong_complete = True
                else:
                    sam_hyeong_partial = True

        axis_patterns: List[AxisPattern] = []
        if any(axis_hits.values()):
            state = "complete" if all(axis_hits.values()) else "partial"
            axis_patterns.append(AxisPattern(pattern="sajeong_chung", state=state))

        if sam_hyeong_complete or sam_hyeong_partial:
            axis_patterns.append(
                AxisPattern(
                    pattern="sam_hyeong",
                    state="complete" if sam_hyeong_complete else "partial",
                )
            )

        return axis_patterns


# ---------------------------------------------------------------------------
# Utility builders
# ---------------------------------------------------------------------------


def build_hidden_role_index(branch_hidden_policy: Mapping[str, Sequence[Mapping[str, object]]]) -> Dict[str, Dict[str, str]]:
    """Return {branch: {stem: role}} mapping from TenGod policy payload."""

    index: Dict[str, Dict[str, str]] = {}
    for branch, entries in branch_hidden_policy.items():
        slot = {}
        for entry in entries or []:
            stem = entry.get("stem")
            role = entry.get("role") or "secondary"
            if stem:
                slot[stem] = str(role)
        if slot:
            index[branch] = slot
    return index
