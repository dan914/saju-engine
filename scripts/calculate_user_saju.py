#!/usr/bin/env python3
"""
Calculate complete Saju analysis for user birth data.
Birth: 2000-09-14 10:00 (양력, 오전 10시)
Location: Seoul, Korea (Asia/Seoul timezone)

Usage:
    poetry run python scripts/calculate_user_saju.py
"""

import json
from datetime import datetime

# Use Poetry-based imports via script loader
from scripts._script_loader import (
    get_analysis_module,
    get_pillars_module,
)

# Load required classes from services
PillarsEngineClass = get_pillars_module("engine", "PillarsEngine")
PillarsComputeRequest = get_pillars_module("pillars", "PillarsComputeRequest")
AnalysisEngine = get_analysis_module("engine", "AnalysisEngine")
KoreanLabelEnricher = get_analysis_module("korean_enricher", "KoreanLabelEnricher")
AnalysisRequest = get_analysis_module("analysis", "AnalysisRequest")


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

    request = PillarsComputeRequest(
        localDateTime=birth_dt,
        timezone=timezone,
        zi_hour_mode="default",
    )

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
    relations = analysis_result.relations
    priority_hit = relations.priority_hit or "(우선순위 없음)"
    print(f"  우선순위 패턴: {priority_hit}")
    if relations.boosts:
        print("  주요 작용:")
        for boost in relations.boosts[:5]:
            label = boost.get("type") or boost.get("id") or boost.get("name") or "패턴"
            formed = boost.get("formed")
            element = boost.get("element")
            details = ", ".join(
                f"{k}={v}" for k, v in boost.items() if k not in {"type", "id", "name", "formed", "element"}
            )
            status = "성립" if formed else "미성립"
            element_note = f" ({element})" if element else ""
            extra = f" [{details}]" if details else ""
            print(f"    - {label}{element_note}: {status}{extra}")
    elif relations.notes:
        for note in relations.notes:
            print(f"    - {note}")
    else:
        print("  (관계 없음)")
    print()

    # Print Strength
    print("💪 강약(強弱) - Strength:")
    print("-" * 80)
    strength = analysis_result.strength
    grade = strength.grade_code or "알 수 없음"
    bucket = strength.bin or "unknown"
    print(f"  등급: {grade} ({bucket})")
    if strength.score is not None:
        print(f"  점수: {strength.score:.2f}")
    if strength.score_normalized is not None:
        print(f"  정규화 점수: {strength.score_normalized:.2f}")
    if strength.details:
        print("  근거:")
        for key, value in strength.details.model_dump(exclude_none=True).items():
            print(f"    {key}: {value}")
    print()

    # Print Structure
    print("🏛️ 격국(格局) - Structure:")
    print("-" * 80)
    structure = analysis_result.structure
    if structure:
        print(f"  주격국: {structure.primary}")
        if structure.confidence is not None:
            print(f"  신뢰도: {structure.confidence}")
        if structure.candidates:
            print("  후보:")
            for candidate in structure.candidates[:3]:
                print(f"    - {candidate}")
    else:
        print("  (격국 정보 없음)")
    print()

    # Print Luck
    print("🔮 대운(大運) - Luck:")
    print("-" * 80)
    if analysis_result.luck.start_age is not None:
        print(f"  대운 시작 나이: {analysis_result.luck.start_age}세")
    luck_direction = (
        analysis_result.luck_direction.direction
        if analysis_result.luck_direction and analysis_result.luck_direction.direction
        else "알 수 없음"
    )
    print(f"  대운 방향: {luck_direction}")
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
    strength_enriched = enriched.get("strength", {})
    if strength_enriched:
        grade = strength_enriched.get("grade_code")
        grade_ko = strength_enriched.get("grade_code_ko")
        bin_label = strength_enriched.get("bin")
        if grade and grade_ko:
            print(f"  등급: {grade} → {grade_ko}")
        elif grade:
            print(f"  등급: {grade}")
        if bin_label:
            print(f"  강약 구간: {bin_label}")
    else:
        print("  (강약 데이터 없음)")
    print()

    # Show enriched Structure
    print("격국 (한국어 보강):")
    print("-" * 80)
    structure_enriched = enriched.get("structure", {})
    if "primary_ko" in structure_enriched:
        print(
            f"  주격국: {structure_enriched['primary']} → {structure_enriched['primary_ko']}"
        )
    elif structure_enriched.get("primary"):
        print(f"  주격국: {structure_enriched['primary']}")
    else:
        print("  (주격국 데이터 없음)")
    if "confidence_ko" in structure_enriched:
        print(
            f"  신뢰도: {structure_enriched['confidence']} → {structure_enriched['confidence_ko']}"
        )
    elif structure_enriched.get("confidence") is not None:
        print(f"  신뢰도: {structure_enriched['confidence']}")
    print()

    # Show enriched Luck Direction
    print("대운 방향 (한국어 보강):")
    print("-" * 80)
    luck_dir_enriched = enriched.get("luck_direction", {})
    if "direction_ko" in luck_dir_enriched:
        print(
            f"  방향: {luck_dir_enriched['direction']} → {luck_dir_enriched['direction_ko']}"
        )
    elif luck_dir_enriched.get("direction"):
        print(f"  방향: {luck_dir_enriched['direction']}")
    else:
        print("  (대운 방향 데이터 없음)")
    print()

    print("=" * 80)
    print("✅ 사주 분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
