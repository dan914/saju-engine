"""
Korean Label Enricher for LLM Payload
======================================

Enriches analysis response payloads with Korean labels (_ko fields) for LLM consumption.
Non-invasive approach: adds Korean labels without modifying original engine outputs.

Version: 1.0.0
Status: Production Ready
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

# Policy file paths (relative to repository root)
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
POLICY_DIR = REPO_ROOT / "saju_codex_batch_all_v2_6_signed" / "policies"

LOCALIZATION_KO_PATH = POLICY_DIR / "localization_ko_v1.json"
GYEOKGUK_POLICY_PATH = POLICY_DIR / "gyeokguk_policy.json"
SHENSHA_POLICY_PATH = POLICY_DIR / "shensha_v2_policy.json"
JIAZI_POLICY_PATH = POLICY_DIR / "sixty_jiazi.json"


@dataclass(slots=True)
class KoreanLabelEnricher:
    """
    Enrich analysis payload with Korean labels for LLM consumption.

    Loads 141 Korean term mappings from policy files:
    - localization_ko_v1.json: 29 items (십신, 강약, 대운방향, 신뢰도, 주, 왕상휴수사, 관계타입, 추천)
    - gyeokguk_policy.json: 14 items (격국)
    - shensha_v2_policy.json: 20 items (신살)
    - sixty_jiazi.json: 60 items (육십갑자)

    Usage:
        enricher = KoreanLabelEnricher.from_files()
        enriched_payload = enricher.enrich(original_payload)
    """

    # From localization_ko_v1.json
    ten_gods_ko: Dict[str, str] = field(default_factory=dict)
    role_ko: Dict[str, str] = field(default_factory=dict)
    relation_ko: Dict[str, str] = field(default_factory=dict)
    strength_ko: Dict[str, str] = field(default_factory=dict)
    luck_direction_ko: Dict[str, str] = field(default_factory=dict)
    confidence_ko: Dict[str, str] = field(default_factory=dict)
    validity_ko: Dict[str, str] = field(default_factory=dict)
    pillar_ko: Dict[str, str] = field(default_factory=dict)
    month_state_ko: Dict[str, str] = field(default_factory=dict)
    relation_types_ko: Dict[str, str] = field(default_factory=dict)
    recommendation_ko: Dict[str, str] = field(default_factory=dict)

    # From policy files
    gyeokguk_ko: Dict[str, str] = field(default_factory=dict)
    shensha_ko: Dict[str, str] = field(default_factory=dict)
    jiazi_ko: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_files(cls) -> "KoreanLabelEnricher":
        """
        Load all Korean mappings from policy files.

        Returns:
            KoreanLabelEnricher instance with all mappings loaded

        Raises:
            FileNotFoundError: If policy files are missing
            json.JSONDecodeError: If policy files are malformed
        """
        # Load localization_ko_v1.json
        with open(LOCALIZATION_KO_PATH, "r", encoding="utf-8") as f:
            loc_data = json.load(f)

        # Load policy files
        gyeokguk_ko = cls._load_gyeokguk_labels()
        shensha_ko = cls._load_shensha_labels()
        jiazi_ko = cls._load_jiazi_labels()

        # Filter out metadata fields (starting with _)
        def clean_dict(d: Dict[str, Any]) -> Dict[str, str]:
            return {k: v for k, v in d.items() if not k.startswith("_")}

        return cls(
            ten_gods_ko=clean_dict(loc_data.get("ten_gods_ko", {})),
            role_ko=clean_dict(loc_data.get("role_ko", {})),
            relation_ko=clean_dict(loc_data.get("relation_ko", {})),
            strength_ko=clean_dict(loc_data.get("strength_ko", {})),
            luck_direction_ko=clean_dict(loc_data.get("luck_direction_ko", {})),
            confidence_ko=clean_dict(loc_data.get("confidence_ko", {})),
            validity_ko=clean_dict(loc_data.get("structure_validity_ko", {})),
            pillar_ko=clean_dict(loc_data.get("pillar_ko", {})),
            month_state_ko=clean_dict(loc_data.get("month_state_ko", {})),
            relation_types_ko=clean_dict(loc_data.get("relation_types_ko", {})),
            recommendation_ko=clean_dict(loc_data.get("recommendation_action_ko", {})),
            gyeokguk_ko=gyeokguk_ko,
            shensha_ko=shensha_ko,
            jiazi_ko=jiazi_ko,
        )

    @staticmethod
    def _load_gyeokguk_labels() -> Dict[str, str]:
        """Load gyeokguk Korean labels from gyeokguk_policy.json."""
        with open(GYEOKGUK_POLICY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        mapping = {}
        for entry in data.get("patterns", []):
            code = entry.get("code")
            label_ko = entry.get("label_ko")
            if code and label_ko:
                mapping[code] = label_ko

        return mapping

    @staticmethod
    def _load_shensha_labels() -> Dict[str, str]:
        """Load shensha Korean labels from shensha_v2_policy.json."""
        with open(SHENSHA_POLICY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        mapping = {}
        for entry in data.get("shensha_catalog", []):
            key = entry.get("key")
            labels = entry.get("labels", {})
            label_ko = labels.get("ko")
            if key and label_ko:
                mapping[key] = label_ko

        return mapping

    @staticmethod
    def _load_jiazi_labels() -> Dict[str, str]:
        """
        Load sixty jiazi Korean labels from sixty_jiazi.json.

        Creates mapping from romanized keys (e.g., "JIAZI") to Korean labels (e.g., "갑자").
        Extracts jiazi part only (without nayin) from label_ko.
        """
        with open(JIAZI_POLICY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        mapping = {}
        for entry in data.get("records", []):
            label_en = entry.get("label_en", "")
            label_ko = entry.get("label_ko", "")

            if not label_en or not label_ko:
                continue

            # Extract romanization from label_en: "Jia-Zi (Metal in the Sea)" -> "JIAZI"
            romanized = label_en.split("(")[0].strip().replace("-", "").upper()

            # Extract jiazi from label_ko: "갑자(해중금)" -> "갑자"
            jiazi_ko = label_ko.split("(")[0].strip() if "(" in label_ko else label_ko

            if romanized and jiazi_ko:
                mapping[romanized] = jiazi_ko

        return mapping

    def enrich(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add Korean labels to payload for LLM consumption.

        Adds *_ko fields alongside original fields without modifying original values.
        Handles missing mappings gracefully by preserving original values.

        Args:
            payload: Original analysis response payload

        Returns:
            Enriched payload with Korean labels added
        """
        # Deep copy to avoid modifying original
        enriched = self._deep_copy(payload)

        # Enrich each section
        self._enrich_ten_gods(enriched)
        self._enrich_structure(enriched)
        self._enrich_strength(enriched)
        self._enrich_luck_direction(enriched)
        self._enrich_shensha(enriched)
        self._enrich_relations(enriched)
        self._enrich_recommendation(enriched)
        self._enrich_pillars(enriched)

        # Add enrichment metadata
        enriched["_enrichment"] = {
            "korean_labels_added": True,
            "locale": "ko-KR",
            "enricher_version": "1.0.0",
            "mappings_count": 141,
        }

        return enriched

    def _enrich_ten_gods(self, payload: Dict[str, Any]) -> None:
        """Enrich ten gods labels in all sections."""
        # Enrich branch_tengods section
        if "branch_tengods" in payload:
            for pillar_data in payload["branch_tengods"].values():
                if isinstance(pillar_data, dict) and "roles" in pillar_data:
                    for role_entry in pillar_data["roles"]:
                        if "tengod" in role_entry:
                            tengod = role_entry["tengod"]
                            role_entry["tengod_ko"] = self.ten_gods_ko.get(tengod, tengod)
                        if "role" in role_entry:
                            role = role_entry["role"]
                            role_entry["role_ko"] = self.role_ko.get(role, role)

    def _enrich_structure(self, payload: Dict[str, Any]) -> None:
        """Enrich gyeokguk (structure) labels."""
        if "structure" in payload:
            struct = payload["structure"]

            # Primary structure
            if "primary" in struct:
                primary = struct["primary"]
                struct["primary_ko"] = self.gyeokguk_ko.get(primary, primary)

            # Secondary structure
            if "secondary" in struct:
                secondary = struct["secondary"]
                struct["secondary_ko"] = self.gyeokguk_ko.get(secondary, secondary)

            # Confidence
            if "confidence" in struct:
                confidence = struct["confidence"]
                struct["confidence_ko"] = self.confidence_ko.get(confidence, confidence)

            # Validity (성격/가격/파격/불성립)
            if "validity" in struct:
                validity = struct["validity"]
                struct["validity_ko"] = self.validity_ko.get(validity, validity)

    def _enrich_strength(self, payload: Dict[str, Any]) -> None:
        """Enrich strength (강약) labels."""
        if "strength" in payload:
            strength = payload["strength"]

            if "level" in strength:
                level = strength["level"]
                strength["level_ko"] = self.strength_ko.get(level, level)

            # Enrich month state if present
            if "month_state" in strength:
                state = strength["month_state"]
                strength["month_state_ko"] = self.month_state_ko.get(state, state)

    def _enrich_luck_direction(self, payload: Dict[str, Any]) -> None:
        """Enrich luck direction (대운 방향) labels."""
        if "luck_direction" in payload:
            luck = payload["luck_direction"]

            if "direction" in luck:
                direction = luck["direction"]
                luck["direction_ko"] = self.luck_direction_ko.get(direction, direction)

    def _enrich_shensha(self, payload: Dict[str, Any]) -> None:
        """Enrich shensha (신살) labels."""
        if "shensha" in payload and "list" in payload["shensha"]:
            for shensha_entry in payload["shensha"]["list"]:
                # Shensha key
                if "key" in shensha_entry:
                    key = shensha_entry["key"]
                    shensha_entry["label_ko"] = self.shensha_ko.get(key, key)

                # Pillar
                if "pillar" in shensha_entry:
                    pillar = shensha_entry["pillar"]
                    shensha_entry["pillar_ko"] = self.pillar_ko.get(pillar, pillar)

    def _enrich_relations(self, payload: Dict[str, Any]) -> None:
        """Enrich relations (관계) labels."""
        if "relations" in payload and "list" in payload["relations"]:
            for relation_entry in payload["relations"]["list"]:
                # Relation type
                if "type" in relation_entry:
                    rel_type = relation_entry["type"]
                    relation_entry["type_ko"] = self.relation_types_ko.get(rel_type, rel_type)

                # Pillars
                if "pillars" in relation_entry:
                    pillars = relation_entry["pillars"]
                    relation_entry["pillars_ko"] = [self.pillar_ko.get(p, p) for p in pillars]

    def _enrich_recommendation(self, payload: Dict[str, Any]) -> None:
        """Enrich recommendation (추천) labels."""
        if "recommendation" in payload:
            rec = payload["recommendation"]

            if "action" in rec:
                action = rec["action"]
                rec["action_ko"] = self.recommendation_ko.get(action, action)

    def _enrich_pillars(self, payload: Dict[str, Any]) -> None:
        """Enrich pillar labels and jiazi labels in pillars section."""
        if "pillars" not in payload:
            return

        for pillar_name, pillar_data in payload["pillars"].items():
            if not isinstance(pillar_data, dict):
                continue

            # Add pillar name Korean label
            pillar_data["pillar_ko"] = self.pillar_ko.get(pillar_name, pillar_name)

            # Enrich jiazi (stem-branch combination)
            if "jiazi" in pillar_data:
                jiazi = pillar_data["jiazi"]
                pillar_data["jiazi_ko"] = self.jiazi_ko.get(jiazi, jiazi)

            # Enrich stem if it's a jiazi key
            if "stem" in pillar_data:
                stem = pillar_data["stem"]
                pillar_data["stem_ko"] = self.jiazi_ko.get(stem, stem)

            # Enrich branch if it's a jiazi key
            if "branch" in pillar_data:
                branch = pillar_data["branch"]
                pillar_data["branch_ko"] = self.jiazi_ko.get(branch, branch)

    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """
        Deep copy without using copy.deepcopy (for performance).

        Handles dict, list, and primitive types.
        """
        if isinstance(obj, dict):
            return {k: KoreanLabelEnricher._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [KoreanLabelEnricher._deep_copy(item) for item in obj]
        else:
            # Primitives (str, int, float, bool, None) are immutable
            return obj
