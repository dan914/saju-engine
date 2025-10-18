# -*- coding: utf-8 -*-
"""
TwelveStagesCalculator v1.0
Calculates the Twelve Life Stages (12운성 / 十二運星) for each pillar.

The Twelve Stages represent the life cycle of each heavenly stem in relation to
the earthly branches:
- 長生 (Birth) - 목욕 (Bath) - 관대 (Crown) - 임관 (Office)
- 제왕 (Peak) - 쇠 (Decline) - 병 (Sickness) - 사 (Death)
- 묘 (Tomb) - 절 (Extinction) - 태 (Embryo) - 양 (Nurture)

Version: 1.0.0
Date: 2025-10-12 KST
Policy: lifecycle_stages.json v1.1
"""
from __future__ import annotations

from typing import Any, Dict


class TwelveStagesCalculator:
    """Calculate Twelve Life Stages for each pillar position."""

    def __init__(self, policy: Dict[str, Any], *, output_policy_version: str = "twelve_stages_v1.0"):
        self.policy = policy
        self.output_policy_version = output_policy_version
        self.mappings = policy["mappings"]
        self.labels = policy.get("labels", {})

    def evaluate(self, pillars: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Calculate Twelve Stages for all four pillars.

        Args:
            pillars = {
              "year": {"stem":"庚", "branch":"辰"},
              "month":{"stem":"乙", "branch":"酉"},
              "day":  {"stem":"乙", "branch":"亥"},
              "hour": {"stem":"辛", "branch":"巳"}
            }

        Returns:
            {
              "policy_version": "twelve_stages_v1.0",
              "by_pillar": {
                "year": {"stem": "庚", "branch": "辰", "stage_zh": "養", "stage_ko": "양", "stage_en": "Nurture"},
                ...
              },
              "summary": {"養": 1, "死": 1, ...},
              "dominant": ["養"],
              "weakest": ["死"]
            }
        """
        out = {
            "policy_version": self.output_policy_version,
            "by_pillar": {},
            "summary": {},
            "dominant": [],
            "weakest": []
        }

        # Calculate stage for each pillar
        for pos in ("year", "month", "day", "hour"):
            stem = pillars[pos]["stem"]
            branch = pillars[pos]["branch"]

            stage_zh = self.mappings.get(stem, {}).get(branch, "未知")
            stage_ko = self._translate(stage_zh, "zh", "ko")
            stage_en = self._translate(stage_zh, "zh", "en")

            out["by_pillar"][pos] = {
                "stem": stem,
                "branch": branch,
                "stage_zh": stage_zh,
                "stage_ko": stage_ko,
                "stage_en": stage_en
            }

            # Count for summary
            if stage_zh != "未知":
                out["summary"][stage_zh] = out["summary"].get(stage_zh, 0) + 1

        # Determine dominant (most common) and weakest stages
        if out["summary"]:
            max_count = max(out["summary"].values())
            out["dominant"] = [k for k, v in out["summary"].items() if v == max_count]

            # Weakest: stages like 死/病/絕
            weak_stages = {"死", "病", "絕", "墓", "衰"}
            out["weakest"] = [k for k in out["summary"].keys() if k in weak_stages]

        return out

    def _translate(self, zh_label: str, from_lang: str, to_lang: str) -> str:
        """Translate stage label between languages."""
        if from_lang != "zh" or zh_label == "未知":
            return zh_label

        zh_labels = self.labels.get("zh", [])
        to_labels = self.labels.get(to_lang, [])

        try:
            idx = zh_labels.index(zh_label)
            return to_labels[idx]
        except (ValueError, IndexError):
            return zh_label
