# -*- coding: utf-8 -*-
"""
TenGodsCalculator v1.0
- 입력: pillars(연/월/일/시: stem/branch), policy(JSON: mapping_rules, ten_gods_labels, relations, branches_hidden)
- 처리: 일간 대비 각 천간/지장간의 십성 판정, 지장간 포함 집계
- 출력: by_pillar, summary, dominant, missing, policy_version, policy_signature
- 서명: RFC-8785 스타일(키정렬+minified) 기반 SHA-256 (CI에서 재검증 권장)
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict

HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

STEM_TO_ELEMENT = {
    "甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"
}
STEM_TO_POLARITY = {
    "甲":"陽","丙":"陽","戊":"陽","庚":"陽","壬":"陽",
    "乙":"陰","丁":"陰","己":"陰","辛":"陰","癸":"陰"
}
TEN_GODS_ENUM_ZH = ["比肩","劫財","食神","傷官","偏財","正財","七殺","正官","偏印","正印"]

class TenGodsCalculator:
    """
    policy 요구 필드:
      - relations: { elements, sheng, ke }
      - mapping_rules: { same_element, wo_sheng, wo_ke, ke_wo, sheng_wo } 각 {same_polarity,diff_polarity} -> code
      - ten_gods_labels: { zh: {code->"比肩"...}, ko/en ... }  (엔진은 zh 사용)
      - branches_hidden: { "辰":[{"stem":"戊","element":"土","role":"primary"}, ...], ... }
    """
    def __init__(self, policy: Dict[str, Any], *, output_policy_version: str = "ten_gods_v1.0"):
        self.policy = policy
        self.output_policy_version = output_policy_version
        # 캐시
        self._ten_gods_label_map_zh = policy["ten_gods_labels"]["zh"]
        self._sheng = policy["relations"]["sheng"]
        self._ke = policy["relations"]["ke"]
        self._mapping = policy["mapping_rules"]
        self._branches_hidden = policy["branches_hidden"]

    # ------------ 공개 API ------------
    def evaluate(self, pillars: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        pillars = {
          "year": {"stem":"庚", "branch":"辰"},
          "month":{"stem":"乙", "branch":"酉"},
          "day":  {"stem":"乙", "branch":"亥"},
          "hour": {"stem":"辛", "branch":"巳"}
        }
        """
        self._validate_input(pillars)

        day_stem = pillars["day"]["stem"]
        out = {
            "policy_version": self.output_policy_version,
            "by_pillar": {},
            "summary": {},
            "dominant": [],
            "missing": [],
            # policy_signature는 마지막에 삽입
        }

        # per pillar
        for slot in ("year","month","day","hour"):
            stem = pillars[slot]["stem"]
            br = pillars[slot]["branch"]
            vs_day = self._rel_label(day_stem, stem)  # 천간 대비 십성(zh)

            hidden_map = {}
            for h in self._branches_hidden.get(br, []):
                hs = h["stem"]
                hidden_map[hs] = self._rel_label(day_stem, hs)

            out["by_pillar"][slot] = {
                "stem": stem,
                "vs_day": vs_day,
                "branch": br,
                "hidden": hidden_map
            }

        # summary 집계 (정수 카운트)
        counts = {}
        for slot_data in out["by_pillar"].values():
            self._bump(counts, slot_data["vs_day"])
            for tg in slot_data["hidden"].values():
                self._bump(counts, tg)
        out["summary"] = counts

        # dominant / missing
        if counts:
            maxv = max(counts.values())
            out["dominant"] = [k for k, v in counts.items() if v == maxv]
        out["missing"] = [tg for tg in TEN_GODS_ENUM_ZH if counts.get(tg, 0) == 0]

        # 최종 서명 삽입
        out["policy_signature"] = self._sha256_canonical(out)

        return out

    # ------------ 내부 로직 ------------
    def _rel_label(self, day_stem: str, target_stem: str) -> str:
        """
        일간 vs 타겟천간 십성 라벨(zh)을 정책 규칙(mapping_rules)에 따라 반환
        """
        e_day = STEM_TO_ELEMENT[day_stem]
        e_tgt = STEM_TO_ELEMENT[target_stem]

        same_elem = (e_day == e_tgt)
        same_polarity = (STEM_TO_POLARITY[day_stem] == STEM_TO_POLARITY[target_stem])

        if same_elem:
            code = self._mapping["same_element"]["same_polarity" if same_polarity else "diff_polarity"]
        elif self._sheng[e_day] == e_tgt:   # 내가 생함(我生)
            code = self._mapping["wo_sheng"]["same_polarity" if same_polarity else "diff_polarity"]
        elif self._ke[e_day] == e_tgt:      # 내가 극함(我克)
            code = self._mapping["wo_ke"]["same_polarity" if same_polarity else "diff_polarity"]
        elif self._ke[e_tgt] == e_day:      # 그가 나를 극함(克我)
            code = self._mapping["ke_wo"]["same_polarity" if same_polarity else "diff_polarity"]
        elif self._sheng[e_tgt] == e_day:   # 그가 나를 생함(生我)
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
        for pos in ("year","month","day","hour"):
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
        """
        RFC-8785 스타일: 키 정렬 + 최소 구분자 (간이 구현).
        policy_signature 필드는 제외하고 해시.
        """
        obj = copy.deepcopy(obj_with_sig)
        obj.pop("policy_signature", None)
        data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
