"""
EngineSummariesBuilder - LLM Guard v1.1 Engine Summaries Pipeline

Aggregates outputs from Strength, Relation, Yongshin, and Climate engines
into the unified `engine_summaries` structure required by LLM Guard v1.1
for cross-engine consistency validation.

Version: 1.0.0
Date: 2025-10-09 KST
"""
from __future__ import annotations

from typing import Any, Dict, List


class EngineSummariesBuilder:
    """
    Builds llm_guard v1.1 `engine_summaries` payload from individual engine outputs.

    Cross-engine consistency rules require unified view of:
    - Strength: score (0-1 normalized), bucket, confidence
    - Relation: sanhe/liuhe/ganhe/chong counts, element results, formation status
    - Yongshin: selected yongshin/bojosin, confidence, strategy
    - Climate: season element, support level

    Usage:
        >>> builder = EngineSummariesBuilder()
        >>> summaries = builder.build(
        ...     strength={"score": 0.65, "bucket": "중화", "confidence": 0.8},
        ...     relation_items=[...],
        ...     yongshin={"yongshin": ["木"], "strategy": "부억"},
        ...     climate={"season_element": "火", "support": "강"}
        ... )
        >>> guard_input = {"engine_summaries": summaries, ...}
    """

    @staticmethod
    def build(
        strength: Dict[str, Any],
        relation_items: List[Dict[str, Any]],
        yongshin: Dict[str, Any],
        climate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build unified engine_summaries structure for LLM Guard v1.1.

        Args:
            strength: Output from StrengthEvaluator
                Required fields: score (0-1), bucket, confidence (optional)
            relation_items: List of relation items from RelationTransformer
                Each item: {type, impact_weight, formed, hua, element, ...}
            yongshin: Output from YongshinAnalyzer
                Required fields: yongshin (list), bojosin (list), confidence
            climate: Output from ClimateEvaluator
                Required fields: season_element, support

        Returns:
            Dict with structure matching schema/llm_guard_input_v1.1.json
            engine_summaries section.

        Example:
            {
                "strength": {"score": 0.65, "bucket": "중화", "confidence": 0.8},
                "relation_summary": {
                    "sanhe": 0.70, "liuhe": 0.0, "ganhe": 0.0,
                    "chong": 0.0, "xing": 0.0, "hai": 0.0,
                    "sanhe_element": "金", "ganhe_result": ""
                },
                "relation_items": [...],
                "yongshin_result": {
                    "yongshin": ["木"], "bojosin": ["水"],
                    "confidence": 0.75, "strategy": "부억"
                },
                "climate": {"season_element": "火", "support": "강"}
            }
        """
        # Normalize strength score to 0-1 if needed
        strength_score = float(strength.get("score", 0.5))
        if strength_score > 1.0:
            # Assume 0-100 scale, normalize to 0-1
            strength_score = strength_score / 100.0

        # Summarize relations by type + extract key results
        relation_summary = {
            "sanhe": 0.0,
            "liuhe": 0.0,
            "ganhe": 0.0,
            "chong": 0.0,
            "xing": 0.0,
            "hai": 0.0,
            "sanhe_element": "",
            "ganhe_result": "",
        }

        for item in relation_items:
            rel_type = item.get("type", "")
            weight = float(item.get("impact_weight", 0.0))

            # Update max weight for each relation type
            if rel_type in relation_summary:
                relation_summary[rel_type] = max(relation_summary[rel_type], weight)

            # Extract element results for sanhe/ganhe
            if rel_type == "sanhe" and not relation_summary["sanhe_element"]:
                # Priority: element field, then b field (result element)
                relation_summary["sanhe_element"] = (
                    item.get("element", "") or item.get("b", "")
                )

            if rel_type == "ganhe" and item.get("hua", False):
                # Ganhe with hua (化) - transformation completed
                relation_summary["ganhe_result"] = (
                    item.get("element", "") or item.get("b", "")
                )

        # Build final structure
        return {
            "strength": {
                "score": strength_score,
                "bucket": strength.get("bucket", "중화"),
                "confidence": float(strength.get("confidence", 0.5)),
            },
            "relation_summary": relation_summary,
            "relation_items": relation_items,  # Pass through full items for detailed validation
            "yongshin_result": {
                "yongshin": yongshin.get("yongshin", []),
                "bojosin": yongshin.get("bojosin", []),
                "confidence": float(yongshin.get("confidence", 0.5)),
                "strategy": yongshin.get("strategy", ""),
            },
            "climate": {
                "season_element": climate.get("season_element", ""),
                "support": climate.get("support", "보통"),
            },
        }

    @staticmethod
    def _calculate_strength_confidence(score: float, bucket: str) -> float:
        """
        Calculate strength confidence based on score distance from bucket boundaries.

        Buckets: 극신강 (80-100), 신강 (60-79), 중화 (40-59), 신약 (20-39), 극신약 (0-19)

        High confidence: score is well within bucket boundaries
        Low confidence: score is near bucket boundaries (transitional)
        """
        # Bucket boundaries
        buckets = {
            "극신강": (80, 100),
            "신강": (60, 79),
            "중화": (40, 59),
            "신약": (20, 39),
            "극신약": (0, 19),
        }

        if bucket not in buckets:
            return 0.5  # Unknown bucket

        min_val, max_val = buckets[bucket]
        bucket_range = max_val - min_val

        # Distance from boundaries
        dist_from_min = abs(score - min_val)
        dist_from_max = abs(score - max_val)
        min_distance = min(dist_from_min, dist_from_max)

        # Normalize to 0-1 confidence
        # Max confidence (0.95) when at bucket center
        # Min confidence (0.60) when at bucket boundary
        confidence = 0.60 + (min_distance / bucket_range) * 0.35

        return round(confidence, 2)

    @staticmethod
    def _calculate_relation_impact_weight(rel_type: str) -> float:
        """
        Calculate impact_weight based on relation type priority.

        Based on traditional 사주 theory:
        - 三合/沖: Highest impact (0.85-0.90)
        - 六合: High impact (0.75)
        - 刑: Medium-high impact (0.70)
        - 破: Medium impact (0.50)
        - 害: Lower impact (0.45)
        """
        weights = {
            "sanhe": 0.85,    # 三合 - Strong combination
            "he6": 0.75,      # 六合 - Harmony
            "chong": 0.90,    # 沖 - Strong clash
            "xing": 0.70,     # 刑 - Punishment
            "po": 0.50,       # 破 - Break
            "hai": 0.45,      # 害 - Harm
        }

        return weights.get(rel_type, 0.60)  # Default for unknown types

    @staticmethod
    def extract_from_analysis_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convenience method to extract engine_summaries from AnalysisEngine output.

        Args:
            result: Full AnalysisResponse dict from AnalysisEngine.analyze()

        Returns:
            engine_summaries dict ready for LLM Guard v1.1 input
        """
        # Extract strength
        raw_score = result.get("strength_details", {}).get("total", 50)
        normalized_score = raw_score / 100.0
        bucket = result.get("strength", {}).get("level", "중화")

        strength = {
            "score": normalized_score,
            "bucket": bucket,
            "confidence": EngineSummariesBuilder._calculate_strength_confidence(
                raw_score, bucket
            ),
        }

        # Extract relations
        relations_data = result.get("relations", {})
        relation_items = []
        for rel_type in ["he6", "sanhe", "chong", "xing", "po", "hai"]:
            items = relations_data.get(rel_type, [])
            for item in items:
                relation_items.append({
                    "type": rel_type,
                    "impact_weight": EngineSummariesBuilder._calculate_relation_impact_weight(
                        rel_type
                    ),
                    "formed": True,
                    "hua": item.get("hua", False),
                    "element": item.get("element", ""),
                    **item
                })

        # Extract yongshin
        yongshin_data = result.get("yongshin", {})
        yongshin = {
            "yongshin": yongshin_data.get("primary", []),
            "bojosin": yongshin_data.get("secondary", []),
            # Use actual confidence from YongshinSelector output
            "confidence": float(yongshin_data.get("confidence", 0.75)),
            "strategy": yongshin_data.get("strategy", ""),
        }

        # Extract climate (if available)
        climate_data = result.get("climate", {})
        climate = {
            "season_element": climate_data.get("season_element", ""),
            "support": climate_data.get("support", "보통"),
        }

        return EngineSummariesBuilder.build(
            strength=strength,
            relation_items=relation_items,
            yongshin=yongshin,
            climate=climate,
        )
