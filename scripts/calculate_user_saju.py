#!/usr/bin/env python3
"""
Calculate complete Saju analysis for user birth data.
Birth: 2000-09-14 10:00 (양력, 오전 10시)
Location: Seoul, Korea (Asia/Seoul timezone)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add services to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "services" / "pillars-service"))
sys.path.insert(0, str(repo_root / "services" / "analysis-service"))

# Import after path setup
from app.core.engine import PillarsEngine as PillarsEngineClass
from app.models.pillars import ComputeRequest

# Switch to analysis-service imports
sys.path.insert(0, str(repo_root / "services" / "analysis-service"))
from app.core.engine import AnalysisEngine
from app.core.korean_enricher import KoreanLabelEnricher
from app.models import AnalysisRequest


def main():
    print("=" * 80)
    print("사주 전체 분석 - 2000년 9월 14일 오전 10시 (양력, 서울)")
    print("=" * 80)
    print()

    # Step 1: Calculate Pillars
    print("📅 STEP 1: 사주 기둥 계산 (Pillars Calculation)")
    print("-" * 80)

    pillars_engine = PillarsEngineClass()

    # Create request
    birth_dt = datetime(2000, 9, 14, 10, 0, 0)
    timezone = "Asia/Seoul"

    request = ComputeRequest(birth_dt=birth_dt, timezone=timezone, zi_hour_mode="default")

    print(f"입력 정보:")
    print(f"  생년월일시: {birth_dt}")
    print(f"  시간대: {timezone}")
    print()

    # Compute pillars
    result = pillars_engine.compute(request)

    print(f"사주 기둥:")
    print(
        f"  년주(年柱): {result.pillars.year.pillar} ({result.pillars.year.pillar[0]} {result.pillars.year.pillar[1]})"
    )
    print(
        f"  월주(月柱): {result.pillars.month.pillar} ({result.pillars.month.pillar[0]} {result.pillars.month.pillar[1]})"
    )
    print(
        f"  일주(日柱): {result.pillars.day.pillar} ({result.pillars.day.pillar[0]} {result.pillars.day.pillar[1]})"
    )
    print(
        f"  시주(時柱): {result.pillars.hour.pillar} ({result.pillars.hour.pillar[0]} {result.pillars.hour.pillar[1]})"
    )
    print()

    print(f"추가 정보:")
    print(f"  일간(日干): {result.pillars.day.pillar[0]}")
    print(f"  월지(月支): {result.pillars.month.pillar[1]}")
    print()

    # Step 2: Analysis
    print("=" * 80)
    print("🔍 STEP 2: 사주 분석 (Saju Analysis)")
    print("-" * 80)
    print()

    analysis_engine = AnalysisEngine()

    # Create analysis request from pillars
    analysis_request = AnalysisRequest(pillars=result.pillars.model_dump(), options={})

    # Run analysis
    analysis_result = analysis_engine.analyze(analysis_request)

    # Print Ten Gods
    print("📊 십신(十神) - Ten Gods:")
    print("-" * 80)
    for pillar, god in analysis_result.ten_gods.summary.items():
        print(f"  {pillar:6s}: {god}")
    print()

    # Print Relations
    print("🔗 관계(關係) - Relations:")
    print("-" * 80)
    if analysis_result.relations.he6:
        print(f"  육합(六合): {analysis_result.relations.he6}")
    if analysis_result.relations.sanhe:
        print(f"  삼합(三合): {analysis_result.relations.sanhe}")
    if analysis_result.relations.chong:
        print(f"  충(沖): {analysis_result.relations.chong}")
    if analysis_result.relations.xing:
        print(f"  형(刑): {analysis_result.relations.xing}")
    if analysis_result.relations.po:
        print(f"  파(破): {analysis_result.relations.po}")
    if analysis_result.relations.hai:
        print(f"  해(害): {analysis_result.relations.hai}")
    if not any(
        [
            analysis_result.relations.he6,
            analysis_result.relations.sanhe,
            analysis_result.relations.chong,
            analysis_result.relations.xing,
            analysis_result.relations.po,
            analysis_result.relations.hai,
        ]
    ):
        print("  (관계 없음)")
    print()

    # Print Strength
    print("💪 강약(強弱) - Strength:")
    print("-" * 80)
    print(f"  일간 세력: {analysis_result.strength.level}")
    print(f"  근거:")
    for key, value in analysis_result.strength.basis.items():
        print(f"    {key}: {value}")
    print()

    # Print Structure
    print("🏛️ 격국(格局) - Structure:")
    print("-" * 80)
    print(f"  주격국: {analysis_result.structure.primary}")
    print(f"  신뢰도: {analysis_result.structure.confidence}")
    if analysis_result.structure.candidates:
        print(f"  후보:")
        for candidate in analysis_result.structure.candidates[:3]:
            print(f"    - {candidate}")
    print()

    # Print Luck
    print("🔮 대운(大運) - Luck:")
    print("-" * 80)
    print(f"  대운 시작 나이: {analysis_result.luck.start_age}세")
    print(f"  대운 방향: {analysis_result.luck_direction.direction}")
    print()

    # Print Shensha
    print("⭐ 신살(神煞) - Shensha:")
    print("-" * 80)
    if analysis_result.shensha.list:
        for item in analysis_result.shensha.list[:10]:  # Show first 10
            print(f"  - {item}")
    else:
        print("  (활성화된 신살 없음)")
    print()

    # Step 3: Korean Enrichment
    print("=" * 80)
    print("🇰🇷 STEP 3: 한국어 라벨 보강 (Korean Label Enrichment)")
    print("-" * 80)
    print()

    enricher = KoreanLabelEnricher.from_files()

    # Convert to dict and enrich
    payload = analysis_result.model_dump()
    enriched = enricher.enrich(payload)

    print("한국어 라벨 추가 완료:")
    print(f"  매핑 개수: {enriched['_enrichment']['mappings_count']}")
    print(f"  로케일: {enriched['_enrichment']['locale']}")
    print()

    # Show enriched Ten Gods
    print("십신 (한국어 보강):")
    print("-" * 80)
    # Note: ten_gods doesn't have individual _ko fields in current implementation
    # This would need branch_tengods which has detailed role info
    print("  (십신 한국어 라벨은 branch_tengods 섹션에서 확인 가능)")
    print()

    # Show enriched Strength
    print("강약 (한국어 보강):")
    print("-" * 80)
    if "level_ko" in enriched.get("strength", {}):
        print(f"  일간 세력: {enriched['strength']['level']} → {enriched['strength']['level_ko']}")
    else:
        print(f"  일간 세력: {enriched['strength']['level']}")
    print()

    # Show enriched Structure
    print("격국 (한국어 보강):")
    print("-" * 80)
    if "primary_ko" in enriched.get("structure", {}):
        print(
            f"  주격국: {enriched['structure']['primary']} → {enriched['structure']['primary_ko']}"
        )
    else:
        print(f"  주격국: {enriched['structure']['primary']}")
    if "confidence_ko" in enriched.get("structure", {}):
        print(
            f"  신뢰도: {enriched['structure']['confidence']} → {enriched['structure']['confidence_ko']}"
        )
    print()

    # Show enriched Luck Direction
    print("대운 방향 (한국어 보강):")
    print("-" * 80)
    if "direction_ko" in enriched.get("luck_direction", {}):
        print(
            f"  방향: {enriched['luck_direction']['direction']} → {enriched['luck_direction']['direction_ko']}"
        )
    else:
        print(f"  방향: {enriched['luck_direction']['direction']}")
    print()

    print("=" * 80)
    print("✅ 사주 분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
