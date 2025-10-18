"""Saju Analysis Orchestrator v1.0

Coordinates all analysis engines in correct dependency order.
Works with actual engine APIs - no wrappers, no adapters.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
from zoneinfo import ZoneInfo

from app.core.climate import ClimateContext, ClimateEvaluator

# Stage-3 engines (MVP policy-driven engines)
from app.core.climate_advice import ClimateAdvice
from app.core.combination_element import normalize_distribution, transform_wuxing
from app.core.engine_summaries import EngineSummariesBuilder
from app.core.evidence_builder import build_evidence  # Function-based API
from app.core.gyeokguk_classifier import GyeokgukClassifier
from app.core.korean_enricher import KoreanLabelEnricher
from app.core.llm_guard import LLMGuard
from app.core.luck import ShenshaCatalog
from app.core.luck_flow import LuckFlow
from app.core.luck_pillars import LuckCalculator
from app.core.pattern_profiler import PatternProfiler
from app.core.recommendation import RecommendationGuard
from app.core.relation_weight import RelationWeightEvaluator
from app.core.relations import RelationContext, RelationTransformer
from app.core.relations_extras import RelationAnalyzer
from app.core.relations_extras import RelationContext as RelationsExtrasContext
from app.core.school import SchoolProfileManager

# Core engines
from app.core.strength_v2 import StrengthEvaluator
from app.core.ten_gods import TenGodsCalculator
from app.core.text_guard import TextGuard
from app.core.twelve_stages import TwelveStagesCalculator

# Meta engines
from app.core.void import apply_void_flags, explain_void
from app.core.yongshin_selector_v2 import YongshinSelector
from app.core.yuanjin import apply_yuanjin_flags, explain_yuanjin

# Season mapping from branch
BRANCH_TO_SEASON = {
    "寅": "봄", "卯": "봄", "辰": "장하",
    "巳": "여름", "午": "여름", "未": "장하",
    "申": "가을", "酉": "가을", "戌": "장하",
    "亥": "겨울", "子": "겨울", "丑": "장하"
}

# Element mapping
STEM_TO_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}

BRANCH_TO_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

# Convert Chinese element names to Korean (for yongshin)
CHINESE_TO_KOREAN_ELEMENT = {
    "木": "목", "火": "화", "土": "토", "金": "금", "水": "수"
}

# Season to Korean element mapping
SEASON_TO_KOREAN_ELEMENT = {
    "봄": "목",    # Spring → Wood
    "여름": "화",  # Summer → Fire
    "가을": "금",  # Autumn → Metal
    "겨울": "수",  # Winter → Water
    "장하": "토"   # Late season → Earth
}

# Grade code to YongshinSelector bin mapping (Source of Truth)
_GRADE_TO_BIN = {
    # Korean codes
    "태강": "strong", "극신강": "strong", "신강": "strong",
    "중화": "balanced",
    "신약": "weak", "태약": "weak", "극신약": "weak",
    # English codes (for compatibility)
    "very_strong": "strong", "strong": "strong",
    "balanced": "balanced",
    "weak": "weak", "very_weak": "weak",
}


class SajuOrchestrator:
    """Main orchestrator for Saju analysis.

    Coordinates 19 engines in dependency order:
    Core Engines:
    1. StrengthEvaluator
    2. RelationTransformer
    3. RelationWeightEvaluator
    4. CombinationElement (합화오행)
    5. ClimateEvaluator
    6. YongshinSelector
    7. LuckCalculator
    8. ShenshaCatalog

    Meta Engines:
    9. VoidCalculator (공망)
    10. YuanjinDetector (원진)
    11. RelationsExtras (banhe_groups)

    Stage-3 Engines (MVP policy-driven):
    12. ClimateAdvice
    13. LuckFlow
    14. GyeokgukClassifier
    15. PatternProfiler

    Post-Processing:
    16. EvidenceBuilder
    17. EngineSummariesBuilder
    18. KoreanLabelEnricher
    19. SchoolProfileManager
    20. RecommendationGuard
    21. LLMGuard
    22. TextGuard
    """

    def __init__(self):
        """Initialize all engines with their factory methods."""
        # Core engines
        self.strength = StrengthEvaluator()  # v2 uses __init__, loads policies internally
        self.relations = RelationTransformer.from_file()
        self.relation_weight = RelationWeightEvaluator()
        self.relations_analyzer = RelationAnalyzer()  # For extras like banhe
        self.climate = ClimateEvaluator.from_file()
        self.yongshin = YongshinSelector()
        self.shensha = ShenshaCatalog()

        # Ten Gods calculator
        import json
        from pathlib import Path
        policy_path = Path("saju_codex_batch_all_v2_6_signed/policies/branch_tengods_policy.json")
        with open(policy_path, encoding="utf-8") as f:
            ten_gods_policy = json.load(f)
        self.ten_gods = TenGodsCalculator(ten_gods_policy, output_policy_version="ten_gods_v1.0")

        # Twelve Stages calculator
        lifecycle_path = Path("saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json")
        with open(lifecycle_path, encoding="utf-8") as f:
            lifecycle_policy = json.load(f)
        self.twelve_stages = TwelveStagesCalculator(lifecycle_policy, output_policy_version="twelve_stages_v1.0")

        # Luck Pillars calculator
        luck_pillars_path = Path("saju_codex_batch_all_v2_6_signed/policies/luck_pillars_policy.json")
        with open(luck_pillars_path, encoding="utf-8") as f:
            luck_pillars_policy = json.load(f)
        self.luck = LuckCalculator(luck_pillars_policy)

        # Stage-3 engines (4 MVP policy-driven engines)
        self.climate_advice = ClimateAdvice()
        self.luck_flow = LuckFlow()
        self.gyeokguk = GyeokgukClassifier()
        self.pattern = PatternProfiler()

        # Post-processing engines
        # Note: build_evidence is a function, not a class
        self.summaries = EngineSummariesBuilder()
        self.korean = KoreanLabelEnricher.from_files()
        self.school = SchoolProfileManager.load()
        self.reco = RecommendationGuard.from_file()
        self.llm_guard = LLMGuard.default()
        self.text_guard = TextGuard.from_file()

    def analyze(
        self,
        pillars: Dict[str, str],
        birth_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run complete Saju analysis.

        Args:
            pillars: {year, month, day, hour} in 60甲子
            birth_context: {birth_dt, gender, timezone}

        Returns:
            Complete analysis result with all engine outputs
        """
        try:
            # 1. Parse and validate inputs
            self._validate_inputs(pillars, birth_context)

            # 2. Decompose pillars
            stems, branches = self._decompose_pillars(pillars)
            season = BRANCH_TO_SEASON.get(branches[1], "unknown")  # month branch

            # 3. Call StrengthEvaluator
            strength_result = self._call_strength(pillars, stems, branches)

            # 4. Call RelationTransformer
            relations_result = self._call_relations(pillars, branches)

            # 5. Call RelationWeightEvaluator (add weights to relations)
            weighted_relations = self._call_relation_weight(
                relations_result, pillars, stems, branches
            )

            # 6. Call RelationsExtras (detect banhe_groups)
            banhe_groups = self._call_relations_extras(branches)

            # 6.5. Call TenGodsCalculator
            ten_gods_result = self._call_ten_gods(pillars)

            # 6.6. Call TwelveStagesCalculator
            twelve_stages_result = self._call_twelve_stages(pillars)

            # 7. Calculate raw elements distribution
            elements_raw = self._calculate_elements(stems, branches, strength_result)

            # 8. Call CombinationElement (transform elements based on weighted relations)
            elements, combination_trace = self._call_combination_element(
                weighted_relations, elements_raw
            )

            # 9. Call ClimateEvaluator
            climate_result = self._call_climate(branches[1])  # month branch

            # 10. Call YongshinSelector (with transformed elements)
            yongshin_result = self._call_yongshin(
                stems[2],  # day stem
                season,
                strength_result,
                weighted_relations,  # Use weighted relations
                climate_result,
                elements  # Use transformed elements
            )

            # 11. Call LuckCalculator
            luck_result = self._call_luck(pillars, birth_context, stems[2])

            # 12. Call ShenshaCatalog
            shensha_result = self._call_shensha()

            # 13. Call VoidCalculator (공망)
            void_result = self._call_void(pillars["day"], branches)

            # 14. Call YuanjinDetector (원진)
            yuanjin_result = self._call_yuanjin(branches)

            # 15. Build Stage-3 context and call Stage-3 engines
            stage3_context = self._build_stage3_context(
                season,
                strength_result,
                weighted_relations,  # Use weighted relations
                climate_result,
                yongshin_result,
                elements  # Use transformed elements
            )
            # Call Stage-3 engines in dependency order
            lf = self.luck_flow.run(stage3_context)
            gk = self.gyeokguk.run({**stage3_context, "luck_flow": lf})
            ca = self.climate_advice.run(stage3_context)
            pp = self.pattern.run({**stage3_context, "luck_flow": lf, "gyeokguk": gk})
            stage3_result = {"luck_flow": lf, "gyeokguk": gk, "climate_advice": ca, "pattern": pp}

            # 16. Combine all results
            combined = {
                "season": season,
                "strength": strength_result,
                "relations": relations_result,
                "relations_weighted": weighted_relations,  # NEW: Weighted relations
                "relations_extras": {"banhe_groups": banhe_groups},  # NEW: Extra relations
                "climate": climate_result,
                "elements_distribution_raw": elements_raw,  # NEW: Raw elements before transformation
                "elements_distribution": elements_raw,  # Use RAW elements (original distribution)
                "elements_distribution_transformed": elements,  # Transformed elements (for reference)
                "combination_trace": combination_trace,  # NEW: Transformation trace
                "yongshin": yongshin_result,
                "luck": luck_result,
                "shensha": shensha_result,
                "void": void_result,
                "yuanjin": yuanjin_result,
                "ten_gods": ten_gods_result,  # NEW: Ten Gods analysis
                "twelve_stages": twelve_stages_result,  # NEW: Twelve Stages analysis
                "stage3": stage3_result
            }

            # 17. Call EvidenceBuilder (collect evidence for all engines)
            evidence_result = self._call_evidence_builder(combined, pillars, birth_context)

            # 18. Call EngineSummariesBuilder (prepare for LLM Guard)
            summaries_result = self._call_engine_summaries(combined, evidence_result)

            # 19. Call KoreanLabelEnricher
            enriched = self.korean.enrich(combined)

            # 20. Add SchoolProfileManager
            school_profile = self.school.get_profile()
            enriched["school_profile"] = school_profile

            # 21. Call RecommendationGuard
            structure_primary = stage3_result.get("gyeokguk", {}).get("classification", "")
            reco_result = self.reco.decide(structure_primary=structure_primary)
            enriched["recommendations"] = reco_result

            # 22. Add evidence and summaries to enriched result
            enriched["evidence"] = evidence_result
            enriched["engine_summaries"] = summaries_result

            # 23. Call LLMGuard (pre-validation if LLM will be used)
            llm_guard_result = self._call_llm_guard(enriched, summaries_result)
            enriched["llm_guard"] = llm_guard_result

            # 24. Call TextGuard (filter any forbidden content)
            text_guard_result = self._call_text_guard(enriched)
            enriched["text_guard"] = text_guard_result

            # 25. Add meta information
            enriched["status"] = "success"
            enriched["meta"] = {
                "orchestrator_version": "1.2.0",  # Upgraded version
                "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
                "engines_used": [
                    "StrengthEvaluator",
                    "RelationTransformer",
                    "RelationWeightEvaluator",  # NEW
                    "RelationsExtras",  # NEW
                    "CombinationElement",  # NEW
                    "ClimateEvaluator",
                    "YongshinSelector",
                    "LuckCalculator",
                    "ShenshaCatalog",
                    "TenGodsCalculator",  # NEW
                    "TwelveStagesCalculator",  # NEW
                    "VoidCalculator",
                    "YuanjinDetector",
                    "Stage3Engines",  # Includes 4 MVP engines
                    "EvidenceBuilder",  # NEW
                    "EngineSummariesBuilder",  # NEW
                    "KoreanLabelEnricher",
                    "SchoolProfileManager",
                    "RecommendationGuard",
                    "LLMGuard",  # NEW
                    "TextGuard"  # NEW
                ]
            }

            return enriched

        except Exception as e:
            import traceback
            return {
                "status": "error",
                "error_message": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }

    # Helper methods for input processing

    def _validate_inputs(self, pillars: Dict[str, str], birth_context: Dict[str, Any]):
        """Validate required inputs."""
        required_pillars = ["year", "month", "day", "hour"]
        for key in required_pillars:
            if key not in pillars:
                raise ValueError(f"Missing pillar: {key}")

        if "birth_dt" not in birth_context:
            raise ValueError("Missing birth_dt in birth_context")

        if "gender" not in birth_context:
            raise ValueError("Missing gender in birth_context")

    def _decompose_pillars(self, pillars: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """Split pillars into stems and branches.

        Returns:
            (stems, branches) - both as lists of 4 elements
        """
        stems = [pillars["year"][0], pillars["month"][0], pillars["day"][0], pillars["hour"][0]]
        branches = [pillars["year"][1], pillars["month"][1], pillars["day"][1], pillars["hour"][1]]
        return stems, branches

    def _count_stems(self, stems: List[str]) -> Dict[str, int]:
        """Count occurrences of each stem."""
        all_stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        counts = {stem: 0 for stem in all_stems}
        for s in stems:
            if s in counts:
                counts[s] += 1
        return counts

    def _calculate_elements(
        self,
        stems: List[str],
        branches: List[str],
        strength_result: Dict
    ) -> Dict[str, float]:
        """Calculate element distribution from stems and branches."""
        # Start with basic counts
        element_counts = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}

        # Count from stems (weight: 1.0 each)
        for stem in stems:
            element = STEM_TO_ELEMENT.get(stem)
            if element:
                element_counts[element] += 1.0

        # Count from branches (weight: 0.5 each)
        for branch in branches:
            element = BRANCH_TO_ELEMENT.get(branch)
            if element:
                element_counts[element] += 0.5

        # Normalize to percentages
        total = sum(element_counts.values())
        if total > 0:
            element_counts = {k: v/total for k, v in element_counts.items()}

        return element_counts

    # Engine-specific call methods

    def _call_strength(
        self,
        pillars: Dict[str, str],
        stems: List[str],
        branches: List[str]
    ) -> Dict[str, Any]:
        """Call StrengthEvaluator v2 with simplified API."""
        # v2 API: evaluate(pillars, season)
        # Returns: {"strength": {score_raw, score, score_normalized, grade_code, bin, phase, details}}
        season = BRANCH_TO_SEASON.get(branches[1], "unknown")
        result = self.strength.evaluate(pillars, season)

        # Extract strength dict from wrapper
        return result.get("strength", result)

    def _call_relations(self, pillars: Dict[str, str], branches: List[str]) -> Dict[str, Any]:
        """Call RelationTransformer with RelationContext."""
        # RelationContext takes branches list and month_branch
        ctx = RelationContext(
            branches=branches,
            month_branch=branches[1]  # Month is index 1
        )
        result = self.relations.evaluate(ctx)

        # Convert RelationResult to dict for orchestrator use
        return {
            "priority_hit": result.priority_hit,
            "transform_to": result.transform_to,
            "boosts": result.boosts,
            "notes": result.notes,
            "extras": result.extras
        }

    def _call_climate(self, month_branch: str) -> Dict[str, Any]:
        """Call ClimateEvaluator with ClimateContext."""
        # ClimateContext needs month_branch and segment
        # Segment defaults to "early" if not specified
        ctx = ClimateContext(
            month_branch=month_branch,
            segment="early"
        )
        return self.climate.evaluate(ctx)

    def _call_yongshin(
        self,
        day_stem: str,
        season: str,
        strength_result: Dict,
        relations_result: Dict,
        climate_result: Dict,
        elements: Dict[str, float]
    ) -> Dict[str, Any]:
        """Call YongshinSelector v2 with simplified dual-output API."""
        # v2 API: select(day_master, strength, relations, climate, elements_dist)

        # Prepare strength payload (v2 expects: bin, score_normalized, grade_code)
        strength_for_v2 = {
            "bin": strength_result.get("bin", "balanced"),
            "score_normalized": strength_result.get("score_normalized", 0.5),
            "grade_code": strength_result.get("grade_code", "중화")
        }

        # Prepare relations payload (v2 expects: flags list)
        priority_hit = relations_result.get("priority_hit", "")
        relation_flags = []
        if priority_hit:
            if "chong" in priority_hit:
                relation_flags.append("chong")
            elif "sanhe" in priority_hit:
                relation_flags.append("sanhe")

        relations_for_v2 = {"flags": relation_flags}

        # Prepare climate payload (v2 expects: season in Korean)
        climate_for_v2 = {"season": season}

        # Convert elements distribution from Chinese (木火土金水) to English (wood/fire/earth/metal/water)
        CHINESE_TO_ENGLISH = {
            "木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water"
        }
        elements_english = {
            CHINESE_TO_ENGLISH.get(k, k): v for k, v in elements.items()
        }

        # Call v2 API
        result = self.yongshin.select(
            day_master=day_stem,
            strength=strength_for_v2,
            relations=relations_for_v2,
            climate=climate_for_v2,
            elements_dist=elements_english
        )

        # v2 returns: {policy_version, integrated, split, rationale}
        # For backward compatibility, also add old-style fields
        integrated = result.get("integrated", {})
        split = result.get("split", {})

        # Map to old output format for compatibility
        primary = integrated.get("primary", {})
        secondary = integrated.get("secondary", {})

        return {
            # New v2 fields
            "policy_version": result.get("policy_version", "yongshin_dual_v1"),
            "integrated": integrated,
            "split": split,
            "rationale": result.get("rationale", []),

            # Old-style compatibility fields
            "yongshin": [primary.get("elem_ko", "")],  # Primary as list
            "bojosin": [secondary.get("elem_ko", "")] if secondary.get("elem_ko") else [],
            "gisin": [],  # Not provided in v2 output
            "confidence": integrated.get("confidence", 0.75),
            "strategy": ""  # Not in v2
        }

    def _call_luck(self, pillars: Dict[str, str], birth_context: Dict[str, Any], day_stem: str) -> Dict[str, Any]:
        """Call LuckCalculator v1.0 to generate decade luck pillars.

        Args:
            pillars: Four pillars dict (str format: "庚辰")
            birth_context: Birth context with birth_dt, gender, timezone
            day_stem: Day stem for Hook labeling (optional, for future use)

        Returns:
            Dict with keys:
                - policy_version: "luck_pillars_v1"
                - direction: "forward" | "reverse"
                - start_age: float (when 대운 starts)
                - method: str (e.g., "solar_term_interval")
                - pillars: list of 10 decade pillars
                - current_luck: dict or null
                - policy_signature: SHA-256 hex
        """
        import sys
        from pathlib import Path as _Path

        # Add services/common to path for saju_common import
        common_path = str(_Path(__file__).resolve().parents[4] / "services" / "common")
        if common_path not in sys.path:
            sys.path.insert(0, common_path)

        from saju_common import BasicTimeResolver, FileSolarTermLoader

        # 1. Parse birth_dt to datetime with timezone
        birth_dt_str = birth_context.get("birth_dt")
        tz = birth_context.get("timezone", "Asia/Seoul")

        if isinstance(birth_dt_str, str):
            birth_dt = datetime.fromisoformat(birth_dt_str.replace("Z", "+00:00"))
            if birth_dt.tzinfo is None:
                birth_dt = birth_dt.replace(tzinfo=ZoneInfo(tz))
        else:
            birth_dt = birth_dt_str

        if birth_dt is None:
            # Fallback: return minimal structure
            return {
                "policy_version": "luck_pillars_v1",
                "direction": "forward",
                "start_age": 0.0,
                "method": "solar_term_interval",
                "pillars": [],
                "current_luck": None,
                "policy_signature": ""
            }

        # 2. Calculate solar terms for start_age (reuse FileSolarTermLoader)
        term_data_path = _Path(__file__).resolve().parents[4] / "data"
        term_loader = FileSolarTermLoader(term_data_path)
        resolver = BasicTimeResolver()

        birth_utc = resolver.to_utc(birth_dt, tz)
        year = birth_utc.year
        terms = list(term_loader.load_year(year)) + list(term_loader.load_year(year + 1))

        next_term = next((e for e in terms if e.utc_time > birth_utc), None)
        prev_term = None
        for entry in terms:
            if entry.utc_time <= birth_utc:
                prev_term = entry
            else:
                break

        solar_terms = {}
        if next_term:
            solar_terms["next_jie_ts"] = next_term.utc_time.isoformat()
        if prev_term:
            solar_terms["prev_jie_ts"] = prev_term.utc_time.isoformat()

        # 3. Calculate current age
        now = datetime.now(ZoneInfo(tz))
        age_years_decimal = (now - birth_dt).total_seconds() / (365.25 * 86400)

        # 4. Build birth_ctx for new LuckCalculator
        gender = birth_context.get("gender", "male").lower()
        if gender in ("m", "M"):
            gender = "male"
        elif gender in ("f", "F"):
            gender = "female"

        birth_ctx = {
            "sex": gender,
            "birth_ts": birth_dt.isoformat(),
            "age_years_decimal": age_years_decimal,
            "luck": {},  # Let policy calculate (no override)
            "solar_terms": solar_terms
        }

        # 5. Convert pillars to new format (str → dict)
        pillars_formatted = {}
        for pos in ("year", "month", "day", "hour"):
            pillar = pillars.get(pos, "")
            if len(pillar) == 2:
                pillars_formatted[pos] = {"stem": pillar[0], "branch": pillar[1]}
            else:
                # Handle missing pillar
                pillars_formatted[pos] = {"stem": "", "branch": ""}

        # 6. Call LuckCalculator v1.0
        try:
            result = self.luck.evaluate(birth_ctx, pillars_formatted)
            return result
        except Exception as e:
            print(f"LuckCalculator.evaluate() failed: {e}, returning empty structure")
            return {
                "policy_version": "luck_pillars_v1",
                "direction": "forward",
                "start_age": 0.0,
                "method": "solar_term_interval",
                "pillars": [],
                "current_luck": None,
                "policy_signature": ""
            }

    def _build_stage3_context(
        self,
        season: str,
        strength_result: Dict,
        relations_result: Dict,
        climate_result: Dict,
        yongshin_result: Dict,
        elements: Dict[str, float]
    ) -> Dict[str, Any]:
        """Build context for Stage-3 engines."""
        # Extract relation flags from RelationResult
        priority_hit = relations_result.get("priority_hit", "")
        relation_flags = []
        if priority_hit:
            # Add the main relation type as a flag
            if "chong" in priority_hit:
                relation_flags.append("chong")
            elif "sanhe" in priority_hit:
                relation_flags.append("sanhe")
            elif "banhe" in priority_hit:
                relation_flags.append("banhe")
            elif "sanhui" in priority_hit:
                relation_flags.append("sanhui")

        # Calculate climate balance_index
        temp_bias = climate_result.get("temp_bias", "neutral")
        humid_bias = climate_result.get("humid_bias", "neutral")
        # Simple numeric conversion for bias
        bias_map = {"cold": -1, "neutral": 0, "hot": 1, "dry": -1, "wet": 1}
        balance_index = abs(bias_map.get(temp_bias, 0)) + abs(bias_map.get(humid_bias, 0))

        # Extract yongshin primary
        yongshin_list = yongshin_result.get("yongshin", [])
        yongshin_primary = yongshin_list[0] if yongshin_list else ""

        return {
            "season": season,
            "strength": {
                "phase": strength_result.get("grade_code", "중화"),
                "elements": elements
            },
            "relation": {
                "flags": relation_flags
            },
            "climate": {
                "flags": [],  # ClimateEvaluator doesn't return flags
                "balance_index": balance_index
            },
            "yongshin": {
                "primary": yongshin_primary
            }
        }

    def _call_shensha(self) -> Dict[str, Any]:
        """Call ShenshaCatalog to get list of enabled shensha."""
        return self.shensha.list_enabled(pro_mode=False)

    def _call_void(self, day_pillar: str, branches: List[str]) -> Dict[str, Any]:
        """Call VoidCalculator to compute void (공망) with full metadata."""
        # Use explain_void() to get complete output with policy_version/signature
        void_explanation = explain_void(day_pillar)

        # Apply void flags to actual branches
        void_branches = void_explanation["kong"]
        void_flags = apply_void_flags(branches, void_branches)

        # Return complete void data (includes policy_version for evidence_builder)
        return {
            **void_explanation,  # Includes: policy_version, policy_signature, day_index, xun_start, kong
            "flags": void_flags,
            "day_pillar": day_pillar
        }

    def _call_yuanjin(self, branches: List[str]) -> Dict[str, Any]:
        """Call YuanjinDetector to detect yuanjin (원진) with full metadata."""
        # Use explain_yuanjin() to get complete output with policy_version/signature
        yuanjin_explanation = explain_yuanjin(branches)

        # Apply yuanjin flags
        yuanjin_flags = apply_yuanjin_flags(branches)

        # Return complete yuanjin data (includes policy_version for evidence_builder)
        return {
            **yuanjin_explanation,  # Includes: policy_version, policy_signature, present_branches, hits, pair_count
            "flags": yuanjin_flags
        }

    def _normalize_strength_score(self, raw: float) -> float:
        """
        Normalize strength score to 0.0-1.0 range.

        StrengthEvaluator outputs scores in range [-100, +100] (typical).
        YongshinSelector expects scores in range [0.0, 1.0].

        Mapping:
            -100 → 0.0 (극신약, extremely weak)
              -22 → 0.39 (신약, weak)
                0 → 0.5 (중화, balanced)
              +50 → 0.75 (신강, strong)
             +100 → 1.0 (극신강, extremely strong)

        Args:
            raw: Raw strength score from StrengthEvaluator

        Returns:
            Normalized score in [0.0, 1.0]
        """
        if raw is None:
            return 0.5  # Default to balanced if unknown

        # Clamp to expected range
        clamped = max(-100.0, min(100.0, float(raw)))

        # Linear normalization: [-100, 100] → [0.0, 1.0]
        normalized = (clamped + 100.0) / 200.0

        return normalized

    def _bin_from_grade(self, grade_code: str) -> str:
        """
        Map grade_code (태강/신강/중화/신약/태약) to bin (strong/balanced/weak).

        This is the Source of Truth for strength classification.
        grade_code comes from StrengthEvaluator's policy-based decision.

        Args:
            grade_code: Strength grade from StrengthEvaluator

        Returns:
            Bin label for YongshinSelector (strong|balanced|weak)
        """
        return _GRADE_TO_BIN.get(grade_code, "balanced")  # Default to balanced if unknown

    # NEW Engine Integration Methods

    def _call_relation_weight(
        self,
        relations_result: Dict[str, Any],
        pillars: Dict[str, str],
        stems: List[str],
        branches: List[str]
    ) -> Dict[str, Any]:
        """Call RelationWeightEvaluator to add weights to detected relations."""
        try:
            # Parse relations from notes field
            # RelationTransformer returns notes like ["chong:巳/亥", "he6:子/丑"]
            pairs_detected = []
            notes = relations_result.get("notes", [])

            for note in notes:
                # Parse format: "type:branch1/branch2" or "type:stem1/stem2"
                if ":" in note and "/" in note:
                    rel_type, participants_str = note.split(":", 1)
                    participants = participants_str.split("/")
                    if len(participants) == 2:
                        pairs_detected.append({
                            "type": rel_type,
                            "participants": participants,
                            "formed": True
                        })

            # Also check extras for additional relations (five_he, zixing)
            extras = relations_result.get("extras", {})
            for extra_type, extra_data in extras.items():
                if isinstance(extra_data, dict) and extra_data:
                    # Handle specific extra formats if they exist
                    pass

            # Build context dict
            context = {
                "heavenly": stems,
                "earthly": branches,
                "month_branch": branches[1],  # Month branch
                "season_element": STEM_TO_ELEMENT.get(stems[2], "")  # Day stem element as proxy
            }

            # Call with correct API
            weighted_result = self.relation_weight.evaluate(
                pairs_detected=pairs_detected,
                context=context
            )
            return weighted_result
        except Exception as e:
            # Fallback to unweighted relations if evaluation fails
            print(f"RelationWeightEvaluator failed: {e}, using unweighted relations")
            return relations_result

    def _call_relations_extras(self, branches: List[str]) -> Dict[str, Any]:
        """Call RelationsAnalyzer to detect banhe_groups and other extras."""
        try:
            ctx = RelationsExtrasContext(branches=branches)
            result = self.relations_analyzer.run(ctx)
            return result
        except Exception as e:
            print(f"RelationsExtras failed: {e}, returning empty dict")
            return {"five_he": {}, "zixing": {}, "banhe": []}

    def _call_ten_gods(self, pillars: Dict[str, str]) -> Dict[str, Any]:
        """Call TenGodsCalculator to determine Ten Gods for each position."""
        try:
            # Convert pillars format from "庚辰" to {"stem": "庚", "branch": "辰"}
            formatted_pillars = {}
            for pos in ("year", "month", "day", "hour"):
                pillar = pillars.get(pos, "")
                if len(pillar) == 2:
                    formatted_pillars[pos] = {"stem": pillar[0], "branch": pillar[1]}
                else:
                    formatted_pillars[pos] = {"stem": "", "branch": ""}

            result = self.ten_gods.evaluate(formatted_pillars)
            return result
        except Exception as e:
            print(f"TenGodsCalculator failed: {e}, returning empty result")
            return {
                "policy_version": "ten_gods_v1.0",
                "by_pillar": {},
                "summary": {},
                "dominant": [],
                "missing": [],
                "policy_signature": ""
            }

    def _call_twelve_stages(self, pillars: Dict[str, str]) -> Dict[str, Any]:
        """Call TwelveStagesCalculator to determine lifecycle stage for each position."""
        try:
            # Convert pillars format from "庚辰" to {"stem": "庚", "branch": "辰"}
            formatted_pillars = {}
            for pos in ("year", "month", "day", "hour"):
                pillar = pillars.get(pos, "")
                if len(pillar) == 2:
                    formatted_pillars[pos] = {"stem": pillar[0], "branch": pillar[1]}
                else:
                    formatted_pillars[pos] = {"stem": "", "branch": ""}

            result = self.twelve_stages.evaluate(formatted_pillars)
            return result
        except Exception as e:
            print(f"TwelveStagesCalculator failed: {e}, returning empty result")
            return {
                "policy_version": "twelve_stages_v1.0",
                "by_pillar": {},
                "summary": {},
                "dominant": [],
                "weakest": []
            }

    def _call_combination_element(
        self,
        weighted_relations: Dict[str, Any],
        elements_raw: Dict[str, float]
    ) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """
        Call CombinationElement to transform element distribution based on relations.

        Returns:
            Tuple of (transformed_elements, transformation_trace)
        """
        try:
            # Transform elements based on weighted relations
            elements_transformed, trace = transform_wuxing(
                relations=weighted_relations,
                dist_raw=elements_raw,
                policy=None  # Use default policy
            )

            # Normalize the transformed distribution
            elements_final = normalize_distribution(elements_transformed)

            return elements_final, trace
        except Exception as e:
            print(f"CombinationElement failed: {e}, using raw elements")
            return elements_raw, []

    def _call_evidence_builder(
        self,
        combined: Dict[str, Any],
        pillars: Dict[str, str],
        birth_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call build_evidence to collect evidence for void/yuanjin/wuxing_adjust."""
        try:
            # Prepare inputs for evidence builder
            inputs = {}

            # Add void evidence if present
            if "void" in combined:
                inputs["void"] = combined["void"]

            # Add yuanjin evidence if present
            if "yuanjin" in combined:
                inputs["yuanjin"] = combined["yuanjin"]

            # Add wuxing_adjust evidence (combination trace)
            if "combination_trace" in combined and "elements_distribution" in combined:
                inputs["wuxing_adjust"] = {
                    "dist": combined["elements_distribution"],
                    "trace": combined["combination_trace"]
                }

            # Call function-based API
            evidence = build_evidence(inputs)
            return evidence
        except Exception as e:
            print(f"build_evidence failed: {e}, returning empty evidence")
            return {"evidence_version": "evidence_v1.0.0", "sections": [], "error": str(e)}

    def _call_engine_summaries(
        self,
        combined: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call EngineSummariesBuilder to prepare summaries for LLM Guard."""
        try:
            # Extract strength data with calculated confidence
            strength_data = combined.get("strength", {})
            raw_score = strength_data.get("total", 50)  # 0-100 scale
            bucket = strength_data.get("grade_code", "중화")

            strength = {
                "score": raw_score / 100.0,  # Normalize to 0-1
                "bucket": bucket,
                "confidence": EngineSummariesBuilder._calculate_strength_confidence(
                    raw_score, bucket
                )  # ✅ Use calculation method (not placeholder)
            }

            # Extract relation items with calculated impact_weight
            relation_items = []
            relations = combined.get("relations_weighted", combined.get("relations", {}))
            for rel_type in ["he6", "sanhe", "chong", "xing", "po", "hai"]:
                items = relations.get(rel_type, [])
                for item in items:
                    relation_items.append({
                        "type": rel_type,
                        "impact_weight": EngineSummariesBuilder._calculate_relation_impact_weight(
                            rel_type
                        ),  # ✅ Use calculation method (not placeholder)
                        "formed": True,
                        "hua": item.get("hua", False),
                        "element": item.get("element", ""),
                        **item
                    })

            # Extract yongshin data (use actual confidence from engine)
            yongshin_data = combined.get("yongshin", {})
            yongshin = {
                "yongshin": yongshin_data.get("yongshin", []),
                "bojosin": yongshin_data.get("bojosin", []),
                "confidence": float(yongshin_data.get("confidence", 0.75)),
                "strategy": yongshin_data.get("strategy", "")
            }

            # Extract climate data
            climate_data = combined.get("climate", {})
            climate = {
                "season_element": combined.get("season", ""),  # Use season as proxy
                "support": climate_data.get("support", "보통")
            }

            # Call static method
            summaries = EngineSummariesBuilder.build(
                strength=strength,
                relation_items=relation_items,
                yongshin=yongshin,
                climate=climate
            )
            return summaries
        except Exception as e:
            print(f"EngineSummariesBuilder.build() failed: {e}, returning minimal summaries")
            return {"error": str(e)}

    def _call_llm_guard(
        self,
        enriched: Dict[str, Any],
        summaries: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LLM Guard integration (designed for LLM enhancement workflow).

        For now, just mark as ready for LLM processing.
        Actual validation happens when LLM enhancement is used.
        """
        try:
            # LLMGuard is designed for validating LLM-generated responses
            # Not applicable until we add LLM enhancement to the workflow
            return {
                "enabled": True,
                "ready_for_llm": True,
                "summaries_available": bool(summaries)
            }
        except Exception as e:
            print(f"LLM Guard setup failed: {e}")
            return {"enabled": False, "error": str(e)}

    def _call_text_guard(self, enriched: Dict[str, Any]) -> Dict[str, Any]:
        """
        Text Guard integration (checks for forbidden terms).

        For now, just mark as available.
        Actual filtering happens when generating text output.
        """
        try:
            # TextGuard.guard() works on text strings, not dicts
            # It will be used when generating text output
            return {
                "enabled": True,
                "guard_available": True,
                "forbidden_terms_count": len(self.text_guard.forbidden_terms)
            }
        except Exception as e:
            print(f"Text Guard setup failed: {e}")
            return {"enabled": False, "error": str(e)}
