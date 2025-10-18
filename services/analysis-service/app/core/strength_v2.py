# -*- coding: utf-8 -*-
"""StrengthEvaluator v2.0 - Five-tier grading with bin/normalization
Implements 극신강/신강/중화/신약/극신약 classification with dual approach support.
"""
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

# Add common to path for policy loader
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "services" / "common"))
from policy_loader import load_policy_json

from .utils_strength_yongshin import elem_of_stem, parse_pillar, ten_god_bucket


class StrengthEvaluator:
    """5-단계 강약 산출 + bin/정규화 포함.

    점수 구성:
      - month_state (旺相休囚死):  +30/+15/0/-15/-30
      - branch_root (통근): main +5, sub +3, minor +0 (+2 if in month branch)
      - stem_visible (십성 가중): resource +10, companion +8, output/wealth/official +6
      - combo_clash (합충해): sanhe +6, liuhe +4, chong -8, hai -4
      - month_stem_effect (월간 영향): assist +10%, leak -10%, counter -15%

    최종:
      - normalize [-70, 120] → [0, 100] → grading tiers → bin
      - score_normalized: 0.0~1.0 (0=극신약, 1=극신강)
    """

    # --- Strength normalization policy (v2) ---
    # 이론적 점수 범위: 정책에서 검증된 구성 요소 범위 합산
    THEORETICAL_MIN: float = -70.0
    THEORETICAL_MAX: float = 120.0

    @property
    def THEORETICAL_RANGE(self) -> float:
        """이론적 범위 계산 (MAX - MIN)"""
        return self.THEORETICAL_MAX - self.THEORETICAL_MIN

    def __init__(self):
        self.wang_map = load_policy_json("seasons_wang_map_v2.json")
        self.zanggan = load_policy_json("zanggan_table.json")["by_branch"]
        self.grading = load_policy_json("strength_grading_tiers_v1.json")
        # Adjustment 5: Sort tiers by min (descending) for defensive grading
        self._tiers_sorted = sorted(self.grading["tiers"], key=lambda t: t["min"], reverse=True)
        # Adjustment 6: Load lifecycle stages policy with variant support
        try:
            self.lifecycle = load_policy_json("lifecycle_stages.json")
            self.variant = self.lifecycle.get("variant", "orthodox")
            self.stage_weights = self.lifecycle.get("weights", {})
            self.damping = self.lifecycle.get("damping", {"on_chong": 1.0, "on_hai": 1.0})
        except Exception:
            self.lifecycle = None
            self.variant = "orthodox"
            self.stage_weights = {}
            self.damping = {"on_chong": 1.0, "on_hai": 1.0}

    # --- normalization ---------------------------------------------------
    def _normalize_strength(self, raw_total: float) -> float:
        """
        [-70, 120] → [0, 100] 선형 정규화 후 클램프.

        이론적 범위를 [0, 100] 스케일로 변환하여 티어 분류에 사용합니다.
        단순 클램핑과 달리, 음수 점수의 정보를 보존합니다.

        Args:
            raw_total: 원시 강약 점수 (이론 범위: -70 ~ 120)

        Returns:
            정규화된 점수 (0 ~ 100)

        Examples:
            -70 → 0.0 (극신약 하한)
            -11 → 31.05 (신약)
            0 → 36.84 (신약)
            50 → 63.16 (신강)
            120 → 100.0 (극신강 상한)
        """
        rng = self.THEORETICAL_RANGE
        if rng <= 0:
            # 정책 오구성 방어: 범위가 유효하지 않으면 중립값 반환
            return 50.0

        # 선형 정규화: (x - min) / range * 100
        normalized = (raw_total - self.THEORETICAL_MIN) / rng * 100.0

        # 최종 클램프 (이론 범위 초과 방어)
        return max(0.0, min(100.0, normalized))

    # --- helpers ---------------------------------------------------------
    def _month_state_score(self, month_branch: str, day_stem: str) -> Tuple[int, str]:
        elem = elem_of_stem(day_stem)
        stage = self.wang_map["by_branch"].get(month_branch, {}).get(elem, "休")
        score = self.wang_map["score_map"][stage]
        # Return score and phase(왕/상/휴/囚/死)
        return score, stage

    def _branch_root_score(
        self, day_stem: str, day_branch: str, other_branches: Iterable[str], month_branch: str
    ) -> int:
        """
        Adjustment 1: Enhanced Branch Root Scoring (동오행 통근)
        - Exact match: main +5, sub +3, minor +0 (+2 if month branch)
        - Same element: main +4, sub +2, minor +1 (+1 if month branch)
        - First match only per branch (no double counting)
        """
        score = 0
        day_elem = elem_of_stem(day_stem)

        for br in [day_branch, *other_branches]:
            info = self.zanggan.get(br, {})
            matched = False

            # 1) 동일 글자 우선 (exact match)
            if info.get("main") == day_stem:
                score += 5
                matched = True
                if br == month_branch:
                    score += 2
            elif day_stem in info.get("sub", []):
                score += 3
                matched = True
                if br == month_branch:
                    score += 2
            elif day_stem in info.get("minor", []):
                # minor 기본 0, 월지면 +2 (Adjustment 4)
                matched = True
                if br == month_branch:
                    score += 2

            if matched:
                continue

            # 2) 동오행 fallback (same element, first match only)
            for role, base in (("main", 4), ("sub", 2), ("minor", 1)):
                hs = info.get(role)
                if not hs:
                    continue
                # zanggan schema: role이 문자열 또는 리스트일 수 있음
                stems = hs if isinstance(hs, list) else [hs]
                if any(elem_of_stem(s) == day_elem for s in stems):
                    score += base
                    if br == month_branch:
                        score += 1
                    break

        return score

    def _stem_visible_score(
        self,
        day_stem: str,
        stems_visible: Iterable[str],
        branch_root: int = 0,
        month_state: int = 0,
    ) -> int:
        """
        Adjustment 2: Refined Ten Gods Weights (십성 가중 정교화) - Conservative Tuning v2.2
        - 강화(+): resource(印, 生我) +10, companion(比/劫, 同氣) +8
        - 감점(-): output(食傷, 我生) -3, wealth(財, 我克) -4, official(官殺, 克我) -5

        Conservative tuning (v2.2):
        - Official weight reduced from -6 to -5 (more realistic average)
        - Multiple official diminishing returns: cap total official penalty at -15
        - No-root protection: if branch_root == 0 AND month_state <= -15, cap officials at -12
        - Final cap: max(-30, min(15, total))

        Traditional principle:
        - Multiple officials have diminishing marginal suppression effect (감가수익)
        - No-root + off-season charts reach official saturation faster
        """
        day_elem = elem_of_stem(day_stem)
        weight_pos = {"resource": 10, "companion": 8}
        weight_neg = {"output": -3, "wealth": -4, "official": -5}

        cats = {"resource": 0, "companion": 0, "output": 0, "wealth": 0, "official": 0}

        for st in stems_visible:
            # 같은 글자(동간) 노출은 companion(+)
            if st == day_stem:
                cats["companion"] += 1
                continue
            cat = ten_god_bucket(
                day_elem, elem_of_stem(st)
            )  # -> resource/companion/output/wealth/official
            if cat in weight_pos:
                cats[cat] += 1
            elif cat in weight_neg:
                cats[cat] += 1

        # Calculate points by category
        pos_points = (
            cats["resource"] * weight_pos["resource"] + cats["companion"] * weight_pos["companion"]
        )
        neg_points = cats["output"] * weight_neg["output"] + cats["wealth"] * weight_neg["wealth"]
        official_points = cats["official"] * weight_neg["official"]

        # Apply diminishing returns cap for multiple officials
        # Stricter cap for no-root + off-season cases
        if branch_root == 0 and month_state <= -15:
            # No-root protection: officials saturate faster
            if official_points < -12:
                official_points = -12
        else:
            # Standard cap
            if official_points < -15:
                official_points = -15

        total = pos_points + neg_points + official_points

        # Final cap: ensure within design range
        return max(-30, min(15, total))

    def _combo_clash_score(self, branches: Iterable[str]) -> int:
        """
        Adjustment 3: Combo/Clash Scoring with Conflict Exclusion (합·충·해 누적+캡)
        - Clash/harm can occur simultaneously; combinations shouldn't apply to clashing branches
        - Accumulate clash/harm, exclude conflicted branches from combinations, add caps
        """
        bset = set(branches)
        score = 0
        CHONG = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
        HAI = [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]
        LIUHE = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]
        SANHE = [("寅", "午", "戌"), ("亥", "卯", "未"), ("申", "子", "辰"), ("巳", "酉", "丑")]

        used = set()

        # 1) 충/해: 모두 누적 (accumulate all)
        for a, b in CHONG:
            if a in bset and b in bset:
                score -= 8
                used.update([a, b])
        for a, b in HAI:
            if a in bset and b in bset:
                score -= 4
                used.update([a, b])

        # 2) 삼합: 충/해로 사용된 지지 제외
        for g in SANHE:
            if all(x in bset for x in g) and not any(x in used for x in g):
                score += 6
                used.update(g)

        # 3) 육합: 충/해 지지 제외
        for a, b in LIUHE:
            if a in bset and b in bset and a not in used and b not in used:
                score += 4
                used.update([a, b])

        # 4) 캡 (cap at -24 to +18)
        return max(-24, min(18, score))

    def _month_stem_effect(self, day_stem: str, month_stem: str, base_score: float) -> float:
        """
        Adjustment 7: Month Stem Effect (already correctly implemented)
        - assist: month generates day (gen_from_other) → +10%
        - leak: day generates month (gen_to_other) → -10%
        - counter: month controls day (ke_from_other) → -15%
        - consume: day controls month (ke_to_other) → -5% (소모)
        """
        from .utils_strength_yongshin import elem_of_stem as e
        from .utils_strength_yongshin import rel_of

        r = rel_of(e(day_stem), e(month_stem))
        adj = 0.0
        if r == "gen_from_other":  # 月生日 → 보강
            adj = +0.10
        elif r == "gen_to_other":  # 日生月 → 누수
            adj = -0.10
        elif r == "ke_from_other":  # 月克日 → 억제(강한 감점)
            adj = -0.15
        elif r == "ke_to_other":  # 日克月 → 소모(경감점)
            adj = -0.05
        return base_score * (1.0 + adj)

    def _day_branch_stage_bonus(
        self, day_stem: str, day_branch: str, all_branches: Iterable[str]
    ) -> int:
        """
        Adjustment 6: Day Branch Lifecycle Stage Bonus (일지 12운성) with variant and damping
        - Supports orthodox (經典) and mirror (陰干隨陽) systems
        - Applies damping when day_branch is in chong/hai relationship
        """
        if not hasattr(self, "lifecycle") or not self.lifecycle:
            return 0

        # Get base stage from mappings
        mappings = self.lifecycle.get("mappings", {})
        stage = mappings.get(day_stem, {}).get(day_branch)

        # Apply variant overlay (mirror system)
        if self.variant == "mirror":
            overlay = self.lifecycle.get("mirror_overlay", {}).get(day_stem, {})
            stage = overlay.get(day_branch, stage)

        if not stage:
            return 0

        # Use weights from policy (not hardcoded)
        val = self.stage_weights.get(stage, 0)

        # Apply damping if day_branch is in chong/hai conflict
        bset = set(all_branches)
        CHONG_PAIRS = [
            ("子", "午"),
            ("丑", "未"),
            ("寅", "申"),
            ("卯", "酉"),
            ("辰", "戌"),
            ("巳", "亥"),
        ]
        HAI_PAIRS = [
            ("子", "未"),
            ("丑", "午"),
            ("寅", "巳"),
            ("卯", "辰"),
            ("申", "亥"),
            ("酉", "戌"),
        ]

        # Check if day_branch is in chong relationship
        if any(
            (a == day_branch and b in bset) or (b == day_branch and a in bset)
            for a, b in CHONG_PAIRS
        ):
            val = round(val * self.damping.get("on_chong", 1.0))

        # Check if day_branch is in hai relationship
        if any(
            (a == day_branch and b in bset) or (b == day_branch and a in bset) for a, b in HAI_PAIRS
        ):
            val = round(val * self.damping.get("on_hai", 1.0))

        return int(val)

    def _grade(self, total_clamped: float) -> str:
        """
        Adjustment 5: Defensive Tier Sorting (등급 경계 정렬)
        Use pre-sorted tiers to ensure correct grading regardless of JSON order
        """
        for tier in self._tiers_sorted:
            if total_clamped >= tier["min"]:
                return tier["name"]
        return "극신약"

    def _bin_of_grade(self, grade: str) -> str:
        return self.grading["bin_map"].get(grade, "balanced")

    # --- public ----------------------------------------------------------
    def evaluate(self, pillars: Dict[str, str], season: str = None) -> Dict[str, Any]:
        ys, yb = parse_pillar(pillars["year"])
        ms, mb = parse_pillar(pillars["month"])
        ds, db = parse_pillar(pillars["day"])
        hs, hb = parse_pillar(pillars["hour"])

        # month_state (needed first for stem_visible protection)
        ms_score, phase = self._month_state_score(mb, ds)

        # branch_root
        br_score = self._branch_root_score(ds, db, [yb, mb, hb], month_branch=mb)

        # stem_visible (with no-root protection)
        sv_score = self._stem_visible_score(
            ds, [ys, ms, hs], branch_root=br_score, month_state=ms_score
        )

        # combo_clash
        cc_score = self._combo_clash_score([yb, mb, db, hb])

        # day branch stage bonus (Adjustment 6) with damping
        stage_bonus = self._day_branch_stage_bonus(ds, db, [yb, mb, db, hb])

        base = ms_score + br_score + sv_score + cc_score + stage_bonus

        # month stem effect
        total = self._month_stem_effect(ds, ms, base)

        # ✅ FIX: 선형 정규화 (기존 단순 클램핑 제거)
        # 이론 범위 [-70, 120]를 [0, 100]으로 정규화하여 음수 점수 정보 보존
        score = self._normalize_strength(total)
        grade = self._grade(score)
        binv = self._bin_of_grade(grade)
        normalized = score / 100.0  # 0.0~1.0 (UI용)

        return {
            "strength": {
                "score_raw": round(total, 2),  # 진단용 원시 점수
                "score": round(score, 2),  # UI 표시용 정규화 점수
                "score_normalized": round(normalized, 4),  # 0-1 스케일
                "grade_code": grade,
                "bin": binv,
                "phase": phase,  # 旺/相/休/囚/死
                "details": {
                    "month_state": ms_score,
                    "branch_root": br_score,
                    "stem_visible": sv_score,
                    "combo_clash": cc_score,
                    "day_branch_stage_bonus": stage_bonus,
                    "month_stem_effect_applied": True,
                },
                "policy": {
                    "min": self.THEORETICAL_MIN,
                    "max": self.THEORETICAL_MAX,
                    "range": self.THEORETICAL_RANGE,
                },
            }
        }
