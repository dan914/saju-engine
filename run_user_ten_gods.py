#!/usr/bin/env python3
"""Test user-provided Ten Gods engine

Usage:
    poetry run python run_user_ten_gods.py
"""
import json

# User's engine code
import copy
import hashlib
from typing import Any, Dict

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

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
STEM_TO_POLARITY = {
    "甲": "陽",
    "丙": "陽",
    "戊": "陽",
    "庚": "陽",
    "壬": "陽",
    "乙": "陰",
    "丁": "陰",
    "己": "陰",
    "辛": "陰",
    "癸": "陰",
}
TEN_GODS_ENUM_ZH = ["比肩", "劫財", "食神", "傷官", "偏財", "正財", "偏官", "正官", "偏印", "正印"]


class TenGodsCalculator:
    def __init__(self, policy: Dict[str, Any], *, output_policy_version: str = "ten_gods_v1.0"):
        self.policy = policy
        self.output_policy_version = output_policy_version
        self._ten_gods_label_map_zh = policy["ten_gods_labels"]["zh"]
        self._sheng = policy["relations"]["sheng"]
        self._ke = policy["relations"]["ke"]
        self._mapping = policy["mapping_rules"]
        self._branches_hidden = policy["branches_hidden"]

    def evaluate(self, pillars: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        self._validate_input(pillars)

        day_stem = pillars["day"]["stem"]
        out = {
            "policy_version": self.output_policy_version,
            "by_pillar": {},
            "summary": {},
            "dominant": [],
            "missing": [],
        }

        for slot in ("year", "month", "day", "hour"):
            stem = pillars[slot]["stem"]
            br = pillars[slot]["branch"]
            vs_day = self._rel_label(day_stem, stem)

            hidden_map = {}
            for h in self._branches_hidden.get(br, []):
                hs = h["stem"]
                hidden_map[hs] = self._rel_label(day_stem, hs)

            out["by_pillar"][slot] = {
                "stem": stem,
                "vs_day": vs_day,
                "branch": br,
                "hidden": hidden_map,
            }

        counts = {}
        for slot_data in out["by_pillar"].values():
            self._bump(counts, slot_data["vs_day"])
            for tg in slot_data["hidden"].values():
                self._bump(counts, tg)
        out["summary"] = counts

        if counts:
            maxv = max(counts.values())
            out["dominant"] = [k for k, v in counts.items() if v == maxv]
        out["missing"] = [tg for tg in TEN_GODS_ENUM_ZH if counts.get(tg, 0) == 0]

        out["policy_signature"] = self._sha256_canonical(out)
        return out

    def _rel_label(self, day_stem: str, target_stem: str) -> str:
        e_day = STEM_TO_ELEMENT[day_stem]
        e_tgt = STEM_TO_ELEMENT[target_stem]

        same_elem = e_day == e_tgt
        same_polarity = STEM_TO_POLARITY[day_stem] == STEM_TO_POLARITY[target_stem]

        if same_elem:
            code = self._mapping["same_element"][
                "same_polarity" if same_polarity else "diff_polarity"
            ]
        elif self._sheng[e_day] == e_tgt:
            code = self._mapping["wo_sheng"]["same_polarity" if same_polarity else "diff_polarity"]
        elif self._ke[e_day] == e_tgt:
            code = self._mapping["wo_ke"]["same_polarity" if same_polarity else "diff_polarity"]
        elif self._ke[e_tgt] == e_day:
            code = self._mapping["ke_wo"]["same_polarity" if same_polarity else "diff_polarity"]
        elif self._sheng[e_tgt] == e_day:
            code = self._mapping["sheng_wo"]["same_polarity" if same_polarity else "diff_polarity"]
        else:
            raise ValueError(f"Unmappable relation: day={day_stem}, target={target_stem}")

        label_zh = self._ten_gods_label_map_zh[code]
        return label_zh

    @staticmethod
    def _bump(d: Dict[str, int], key: str) -> None:
        if not key:
            return
        d[key] = d.get(key, 0) + 1

    @staticmethod
    def _validate_input(pillars: Dict[str, Dict[str, str]]) -> None:
        for pos in ("year", "month", "day", "hour"):
            if pos not in pillars:
                raise ValueError(f"Missing pillar: {pos}")
            st = pillars[pos].get("stem")
            br = pillars[pos].get("branch")
            if st not in HEAVENLY_STEMS:
                raise ValueError(f"Invalid stem at {pos}: {st}")
            if br not in EARTHLY_BRANCHES:
                raise ValueError(f"Invalid branch at {pos}: {br}")

    @staticmethod
    def _sha256_canonical(obj_with_sig: Dict[str, Any]) -> str:
        obj = copy.deepcopy(obj_with_sig)
        obj.pop("policy_signature", None)
        data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


# Load our actual policy
with open("saju_codex_batch_all_v2_6_signed/policies/branch_tengods_policy.json") as f:
    policy = json.load(f)

# Test with 2000-09-14 case
pillars = {
    "year": {"stem": "庚", "branch": "辰"},
    "month": {"stem": "乙", "branch": "酉"},
    "day": {"stem": "乙", "branch": "亥"},
    "hour": {"stem": "辛", "branch": "巳"},
}

print("Testing user's Ten Gods engine with our policy...")
print()

engine = TenGodsCalculator(policy, output_policy_version="ten_gods_v1.0")
result = engine.evaluate(pillars)

print("=" * 80)
print("OUTPUT")
print("=" * 80)
print(json.dumps(result, ensure_ascii=False, indent=2))
print()

print("=" * 80)
print("VALIDATION")
print("=" * 80)
print(f"✅ Policy version: {result['policy_version']}")
print(f"✅ Pillars processed: {len(result['by_pillar'])} pillars")
print(f"✅ Summary counts: {len(result['summary'])} types")
print(f"✅ Dominant: {result['dominant']}")
print(f"✅ Missing: {result['missing']}")
print(f"✅ Signature: {result['policy_signature'][:16]}...")
print()

# Verify specific expectations
assert result["by_pillar"]["day"]["vs_day"] == "比肩"
assert "正官" in result["summary"]
print("✅ All assertions passed!")
