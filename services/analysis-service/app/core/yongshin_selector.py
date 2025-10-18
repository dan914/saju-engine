"""
Yongshin Selector v1.0

용신(用神) 자동 선택 엔진:
- Strength-based preference (신약/중화/신강)
- Relation bias (삼합/충/간합 etc.)
- Climate bias (season support)
- Distribution bias (element deficit/excess)

Input: day_master, strength, elements_distribution, relation_summary, climate
Output: yongshin[], bojosin[], gisin[], confidence, rationale[]
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

POLICY_VERSION = "yongshin_v1.0.0"


class YongshinSelector:
    """
    용신 선택기 - 정책 기반 결정론적 용신 산출

    알고리즘:
    1. Strength bin 판정 (weak/balanced/strong)
    2. Base preferences 점수 초기화
    3. Relation bias 적용
    4. Climate bias 적용
    5. Distribution bias 적용
    6. 정렬 후 yongshin/bojosin/gisin 결정
    7. Confidence 계산
    """

    def __init__(self, policy_path: Optional[str] = None):
        """
        Initialize Yongshin Selector with policy.

        Args:
            policy_path: Path to yongshin_selector_policy_v1.json
        """
        if policy_path is None:
            # From app/core/ → app → analysis-service → services → 사주
            repo_root = Path(__file__).resolve().parents[4]
            policy_path = str(repo_root / "policy" / "yongshin_selector_policy_v1.json")

        self.policy = self._load_policy(policy_path)
        self.five_elements = self.policy["five_elements"]
        self.cycles = self.policy["cycle_maps"]

    @staticmethod
    def _load_policy(path: str) -> Dict[str, Any]:
        """Load and validate policy JSON."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def select(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: select yongshin from input.

        Args:
            input_data: Dict with keys:
                - day_master_gan, day_master_element
                - strength: {score, type}
                - elements_distribution: {목, 화, 토, 금, 수}
                - relation_summary: {sanhe, chong, ganhe, ...}
                - climate: {season_element, support}
                - shensha: []
                - context: {month_branch, strict}

        Returns:
            Dict with keys:
                - policy_version
                - yongshin: [] (1-2 elements)
                - bojosin: [] (0-2 elements)
                - gisin: [] (1-2 elements)
                - confidence: float
                - rationale: []
                - scores: {목, 화, 토, 금, 수}
                - rules_fired: []
                - explain: str
        """
        # Extract inputs
        day_element = input_data["day_master_element"]
        strength = input_data["strength"]
        elements_dist = input_data["elements_distribution"]
        relation_summary = input_data["relation_summary"]
        climate = input_data["climate"]

        # 1. Determine strength bin (multi-layer defense: bin → score_normalized → score_raw)
        strength_bin = self._get_strength_bin(strength)
        rules_fired = [f"BIN:{strength_bin}"]

        # 2. Initialize scores
        scores = {e: 0.0 for e in self.five_elements}

        # 3. Apply base preferences
        self._apply_base_preferences(scores, day_element, strength_bin, rules_fired)

        # 4. Apply relation bias
        self._apply_relation_bias(scores, relation_summary, rules_fired)

        # 5. Apply climate bias
        self._apply_climate_bias(scores, day_element, climate, rules_fired)

        # 6. Apply distribution bias
        self._apply_distribution_bias(scores, elements_dist, rules_fired)

        # 7. Sort and categorize
        yongshin, bojosin, gisin = self._categorize_elements(scores)

        # 8. Calculate confidence
        confidence = self._calculate_confidence(
            strength_bin,
            relation_summary.get("relation_hits", 0),
            relation_summary.get("relation_misses", 0),
            climate
        )

        # 9. Generate rationale
        rationale = self._generate_rationale(
            strength_bin, yongshin, gisin, relation_summary, climate, elements_dist
        )

        # 10. Generate explain
        explain = self._generate_explain(strength_bin, yongshin, relation_summary)

        return {
            "policy_version": POLICY_VERSION,
            "yongshin": yongshin,
            "bojosin": bojosin,
            "gisin": gisin,
            "confidence": round(confidence, 2),
            "rationale": rationale,
            "scores": {e: round(scores[e], 2) for e in self.five_elements},
            "rules_fired": rules_fired,
            "explain": explain
        }

    def _auto_normalize(self, score: float) -> float:
        """
        Fallback normalization if orchestrator didn't normalize.

        Assumes StrengthEvaluator range [-100, 100] → [0.0, 1.0]
        This provides a safety net for backward compatibility.
        """
        if score is None:
            return 0.5  # Default to balanced if unknown

        # Clamp to expected range
        clamped = max(-100.0, min(100.0, float(score)))

        # Linear normalization: [-100, 100] → [0.0, 1.0]
        normalized = (clamped + 100.0) / 200.0

        return normalized

    def _get_strength_bin(self, strength: dict) -> str:
        """
        Map strength to bin (weak/balanced/strong) with multi-layer defense.

        Priority:
        1. Use bin if provided (Source of Truth from grade_code)
        2. Use score_normalized if provided
        3. Auto-normalize score_raw as fallback

        Args:
            strength: Dict with keys: bin, score_normalized, score_raw, score (deprecated), type

        Returns:
            "weak" | "balanced" | "strong"
        """
        # Priority 1: bin (Source of Truth from grade_code)
        bin_value = (strength or {}).get("bin")
        if bin_value in ("weak", "balanced", "strong"):
            return bin_value

        # Priority 2: score_normalized
        score_normalized = (strength or {}).get("score_normalized")
        if isinstance(score_normalized, (int, float)):
            score = float(score_normalized)
        else:
            # Priority 3: auto-normalize score_raw (or deprecated "score")
            score_raw = (strength or {}).get("score_raw") or (strength or {}).get("score")
            score = self._auto_normalize(score_raw)

        # Apply policy binning
        binning = self.policy["strength_binning"]
        weak_min, weak_max = binning["weak"]
        balanced_min, balanced_max = binning["balanced"]

        if weak_min <= score < weak_max:
            return "weak"
        if balanced_min <= score < balanced_max:
            return "balanced"
        return "strong"

    def _apply_base_preferences(self, scores: Dict[str, float], day_element: str,
                                strength_bin: str, rules_fired: List[str]) -> None:
        """
        Apply base preferences based on strength bin.

        Preferences map to ten gods relationships:
        - resource: 印(생我) → element that generates day_element
        - companion: 比劫(同我) → same element as day_element
        - output: 食傷(我生) → element generated by day_element
        - wealth: 財(我克) → element controlled by day_element
        - official: 官(克我) → element that controls day_element
        """
        preferences = self.policy["base_preferences"][strength_bin]

        # Define bonuses for each category
        bonuses = {
            "resource": 0.18,
            "companion": 0.12,
            "output": 0.15,
            "wealth": 0.12,
            "official": 0.10
        }

        # Map preferences to elements
        element_map = {
            "resource": self.cycles["generated_by"][day_element],
            "companion": day_element,
            "output": self.cycles["generates"][day_element],
            "wealth": self.cycles["controls"][day_element],
            "official": self.cycles["controlled_by"][day_element]
        }

        for pref in preferences:
            if pref in element_map:
                target_element = element_map[pref]
                scores[target_element] += bonuses.get(pref, 0.0)
                rules_fired.append(f"BASE:{pref}→{target_element}")

    def _apply_relation_bias(self, scores: Dict[str, float],
                            relation_summary: Dict[str, Any],
                            rules_fired: List[str]) -> None:
        """Apply relation bias rules (sanhe, chong, ganhe, etc.)."""
        bias_rules = self.policy["relation_bias_rules"]

        for rule in bias_rules:
            when = rule["when"]
            apply_spec = rule["apply"]

            rel_type = when["type"]
            min_weight = when.get("min_weight", 0.0)
            rel_weight = relation_summary.get(rel_type, 0.0)

            # Check if rule applies
            if rel_weight < min_weight:
                continue

            # Check hua condition for ganhe
            if rel_type == "ganhe" and when.get("hua"):
                if not relation_summary.get("ganhe_result"):
                    continue

            # Determine target element
            toward = apply_spec["toward"]
            delta = apply_spec["delta"]

            target_element = None

            if toward == "sanhe_element":
                target_element = relation_summary.get("sanhe_element")
            elif toward == "ganhe_result":
                target_element = relation_summary.get("ganhe_result")
            elif toward == "liuhe_softening":
                # Liuhe softening: apply small bonus to all elements
                for e in self.five_elements:
                    scores[e] += delta
                rules_fired.append(f"REL:{rel_type}→전체완화")
                continue
            elif toward in ["inside_combo_target", "obstructed_element", "opposite_of_sanhe_if_any"]:
                # These require more context - skip for v1.0
                continue

            if target_element and target_element in self.five_elements:
                scores[target_element] += delta
                rules_fired.append(f"REL:{rel_type}→{target_element}")

    def _apply_climate_bias(self, scores: Dict[str, float], day_element: str,
                           climate: Dict[str, Any], rules_fired: List[str]) -> None:
        """Apply climate bias (season support/conflict)."""
        season_element = climate["season_element"]
        support_label = climate["support"]

        bias_config = self.policy["climate_bias"]

        # Check if season supports day_element
        if season_element == day_element:
            # Same element
            delta = bias_config["if_season_supports"]
            scores[season_element] += delta
            rules_fired.append(f"CLIMATE:same→{season_element}")
        elif self.cycles["generates"][season_element] == day_element:
            # Season generates day_element
            delta = bias_config["if_season_supports"]
            scores[season_element] += delta
            rules_fired.append(f"CLIMATE:support→{season_element}")
        elif self.cycles["controls"][season_element] == day_element:
            # Season controls day_element
            delta = bias_config["if_season_conflicts"]
            scores[season_element] += delta
            rules_fired.append(f"CLIMATE:conflict→{season_element}")

        # Apply support label bonus
        support_delta = bias_config["support_labels"].get(support_label, 0.0)
        if support_delta != 0.0:
            scores[season_element] += support_delta
            rules_fired.append(f"CLIMATE:support_label[{support_label}]")

    def _apply_distribution_bias(self, scores: Dict[str, float],
                                 elements_dist: Dict[str, float],
                                 rules_fired: List[str]) -> None:
        """Apply distribution bias (deficit/excess correction)."""
        bias_config = self.policy["distribution_bias"]
        target_ratio = bias_config["target_ratio"]
        deficit_gain = bias_config["deficit_gain_per_0p10"]
        excess_penalty = bias_config["excess_penalty_per_0p10"]

        for element in self.five_elements:
            actual = elements_dist.get(element, 0.0)
            diff = target_ratio - actual

            if diff > 0:
                # Deficit: boost this element
                delta = (diff / 0.10) * deficit_gain
                scores[element] += delta
                if abs(delta) > 0.01:
                    rules_fired.append(f"DIST:deficit[{element}]")
            elif diff < 0:
                # Excess: penalize this element
                delta = (abs(diff) / 0.10) * excess_penalty
                scores[element] += delta
                if abs(delta) > 0.01:
                    rules_fired.append(f"DIST:excess[{element}]")

    def _categorize_elements(self, scores: Dict[str, float]) -> Tuple[List[str], List[str], List[str]]:
        """
        Sort elements by score and categorize.

        Returns:
            (yongshin, bojosin, gisin)
        """
        caps = self.policy["caps"]
        max_candidates = caps["max_candidates"]
        min_gap = caps["min_primary_score_gap"]

        # Sort by score descending
        sorted_elements = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Top 1-2 as yongshin
        yongshin = [sorted_elements[0][0]]
        if len(sorted_elements) > 1:
            top_score = sorted_elements[0][1]
            second_score = sorted_elements[1][1]
            if (top_score - second_score) < min_gap:
                # Close scores: include both
                yongshin.append(sorted_elements[1][0])

        # Bottom 1-2 as gisin
        gisin = [sorted_elements[-1][0]]
        if len(sorted_elements) > 2:
            bottom_score = sorted_elements[-1][1]
            second_bottom_score = sorted_elements[-2][1]
            if abs(bottom_score - second_bottom_score) < min_gap:
                gisin.insert(0, sorted_elements[-2][0])

        # Middle as bojosin
        bojosin = []
        for element, score in sorted_elements:
            if element not in yongshin and element not in gisin:
                bojosin.append(element)

        # Limit counts
        yongshin = yongshin[:max_candidates]
        bojosin = bojosin[:max_candidates]
        gisin = gisin[:max_candidates]

        return yongshin, bojosin, gisin

    def _calculate_confidence(self, strength_bin: str, relation_hits: int,
                             relation_misses: int, climate: Dict[str, Any]) -> float:
        """Calculate confidence score."""
        conf_model = self.policy["confidence_model"]

        base = conf_model["base"][strength_bin]
        relation_bonus = relation_hits * conf_model["relation_bonus_per_hit"]
        relation_penalty = relation_misses * conf_model["relation_penalty_per_miss"]
        climate_bonus = conf_model["climate_bonus"] if climate.get("support") == "강함" else 0.0

        confidence = base + relation_bonus + relation_penalty + climate_bonus

        # Clamp
        cap_min = conf_model["cap_min"]
        cap_max = conf_model["cap_max"]
        return max(cap_min, min(cap_max, confidence))

    def _generate_rationale(self, strength_bin: str, yongshin: List[str], gisin: List[str],
                           relation_summary: Dict[str, Any], climate: Dict[str, Any],
                           elements_dist: Dict[str, float]) -> List[str]:
        """Generate human-readable rationale."""
        rationale = []

        # Strength-based
        strength_map = {
            "weak": "신약 → 인성·비겁 선호",
            "balanced": "중화 → 균형 유지 선호",
            "strong": "신강 → 식상·관·재 선호"
        }
        rationale.append(strength_map.get(strength_bin, ""))

        # Relation-based
        if relation_summary.get("sanhe", 0.0) > 0.7:
            sanhe_elem = relation_summary.get("sanhe_element", "")
            if sanhe_elem:
                rationale.append(f"삼합({sanhe_elem})이 강력하게 작용")

        if relation_summary.get("ganhe", 0.0) > 0.6:
            ganhe_result = relation_summary.get("ganhe_result", "")
            if ganhe_result:
                rationale.append(f"간합 화(化) {ganhe_result} 성립")

        if relation_summary.get("chong", 0.0) > 0.5:
            rationale.append("충(沖) 강함 → 완충 필요")

        # Climate-based
        support = climate.get("support", "")
        if support == "강함":
            rationale.append(f"계절 {climate['season_element']} 유리")
        elif support == "약함":
            rationale.append(f"계절 {climate['season_element']} 불리")

        # Distribution-based
        max_elem = max(elements_dist, key=elements_dist.get)
        if elements_dist[max_elem] > 0.30 and max_elem in gisin:
            rationale.append(f"{max_elem} 과다 억제 필요")

        return rationale

    def _generate_explain(self, strength_bin: str, yongshin: List[str],
                         relation_summary: Dict[str, Any]) -> str:
        """Generate concise explanation."""
        strength_label = {"weak": "신약형", "balanced": "중화형", "strong": "신강형"}[strength_bin]

        yongshin_str = "·".join(yongshin)

        # Check dominant relation
        dominant_rel = None
        if relation_summary.get("sanhe", 0.0) > 0.7:
            dominant_rel = f"삼합({relation_summary.get('sanhe_element', '')})"
        elif relation_summary.get("ganhe", 0.0) > 0.6:
            dominant_rel = f"간합 화({relation_summary.get('ganhe_result', '')})"
        elif relation_summary.get("chong", 0.0) > 0.5:
            dominant_rel = "충(沖)"

        if dominant_rel:
            return f"{strength_label}으로 {yongshin_str} 선호. {dominant_rel} 영향."
        else:
            return f"{strength_label}으로 {yongshin_str} 선호."


# Convenience function for standalone usage
def select_yongshin(input_data: Dict[str, Any], policy_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Standalone function to select yongshin.

    Args:
        input_data: Input dictionary (see YongshinSelector.select for schema)
        policy_path: Optional path to policy file

    Returns:
        Output dictionary with yongshin, bojosin, gisin, confidence, etc.
    """
    selector = YongshinSelector(policy_path=policy_path)
    return selector.select(input_data)
