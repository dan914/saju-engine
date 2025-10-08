#!/usr/bin/env python3
"""
Complete Saju Analysis for 2000-09-14 10:00 AM
Using all available engines
"""

import sys
from pathlib import Path

# Setup path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "services" / "analysis-service"))

from app.core.engine import AnalysisEngine
from app.core.korean_enricher import KoreanLabelEnricher
from app.models import AnalysisRequest
from app.models.analysis import PillarInput

def main():
    print("=" * 80)
    print("사주 전체 분석 - 2000년 9월 14일 오전 10시 (양력, 서울)")
    print("=" * 80)
    print()

    # 사주 기둥 (Four Pillars)
    # 2000-09-14 10:00 Seoul timezone
    # 만세력 기준 계산 값
    print("📅 사주 기둥 (Four Pillars):")
    print("-" * 80)

    pillars_data = {
        "year": PillarInput(pillar="庚辰"),   # 2000년 = 경진년
        "month": PillarInput(pillar="乙酉"),  # 음력 8월(양력 9월 백로 후) = 을유월
        "day": PillarInput(pillar="丁巳"),     # 일주 (만세력 필요)
        "hour": PillarInput(pillar="乙巳")    # 10시 = 사시 (巳時)
    }

    print(f"년주(年柱): {pillars_data['year'].pillar} (庚辰 경진)")
    print(f"월주(月柱): {pillars_data['month'].pillar} (乙酉 을유)")
    print(f"일주(日柱): {pillars_data['day'].pillar} (丁巳 정사)")
    print(f"시주(時柱): {pillars_data['hour'].pillar} (乙巳 을사)")
    print()
    print(f"일간(日干): {pillars_data['day'].pillar[0]} (丁 정화)")
    print(f"월지(月支): {pillars_data['month'].pillar[1]} (酉 유금)")
    print()

    # Run Analysis
    print("=" * 80)
    print("🔍 사주 분석 (Saju Analysis)")
    print("-" * 80)
    print()

    engine = AnalysisEngine()
    request = AnalysisRequest(pillars=pillars_data, options={})
    result = engine.analyze(request)

    # Ten Gods
    print("📊 십신(十神) - Ten Gods:")
    print("-" * 80)
    for pillar, god in result.ten_gods.summary.items():
        pillar_name = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}.get(pillar, pillar)
        print(f"  {pillar_name:6s}: {god}")
    print()

    # Relations
    print("🔗 관계(關係) - Relations:")
    print("-" * 80)
    relations = result.relations
    has_relation = False
    if relations.he6:
        print(f"  육합(六合): {relations.he6}")
        has_relation = True
    if relations.sanhe:
        print(f"  삼합(三合): {relations.sanhe}")
        has_relation = True
    if relations.chong:
        print(f"  충(沖): {relations.chong}")
        has_relation = True
    if relations.xing:
        print(f"  형(刑): {relations.xing}")
        has_relation = True
    if relations.po:
        print(f"  파(破): {relations.po}")
        has_relation = True
    if relations.hai:
        print(f"  해(害): {relations.hai}")
        has_relation = True
    if not has_relation:
        print("  (특별한 관계 없음)")
    print()

    # Strength
    print("💪 강약(強弱) - Strength:")
    print("-" * 80)
    print(f"  일간 세력: {result.strength.level}")
    print(f"  근거:")
    for key, value in result.strength.basis.items():
        print(f"    {key}: {value}")
    print()

    # Strength Details
    print("  상세 분석:")
    details = result.strength_details
    if hasattr(details, "score"):
        print(f"    점수: {details.score}")
    if hasattr(details, "grade"):
        print(f"    등급: {details.grade}")
    print()

    # Structure
    print("🏛️ 격국(格局) - Structure:")
    print("-" * 80)
    print(f"  주격국: {result.structure.primary}")
    print(f"  신뢰도: {result.structure.confidence}")
    if result.structure.candidates:
        print(f"  후보격국:")
        for i, candidate in enumerate(result.structure.candidates[:5], 1):
            print(f"    {i}. {candidate}")
    print()

    # Luck
    print("🔮 대운(大運) - Luck:")
    print("-" * 80)
    print(f"  대운 시작 나이: {result.luck.start_age}세")
    print(f"  대운 방향: {result.luck_direction.direction}")
    print()

    # Shensha
    print("⭐ 신살(神煞) - Shensha:")
    print("-" * 80)
    if hasattr(result.shensha, "list") and result.shensha.list:
        print(f"  활성화된 신살 (상위 10개):")
        for item in result.shensha.list[:10]:
            print(f"    - {item}")
    else:
        print("  (활성화된 신살 정보 없음)")
    print()

    # School Profile
    print("🏫 학파 프로필 (School Profile):")
    print("-" * 80)
    if result.school_profile:
        profile = result.school_profile
        if hasattr(profile, "name"):
            print(f"  학파: {profile.name}")
        if hasattr(profile, "description"):
            print(f"  설명: {profile.description}")
    else:
        print("  (학파 프로필 정보 없음)")
    print()

    # Korean Enrichment
    print("=" * 80)
    print("🇰🇷 한국어 라벨 보강 (Korean Label Enrichment)")
    print("-" * 80)
    print()

    enricher = KoreanLabelEnricher.from_files()
    payload = result.model_dump()
    enriched = enricher.enrich(payload)

    print("보강 정보:")
    print(f"  총 매핑 개수: {enriched['_enrichment']['mappings_count']}")
    print(f"  로케일: {enriched['_enrichment']['locale']}")
    print(f"  버전: {enriched['_enrichment']['enricher_version']}")
    print()

    # Show enriched fields
    print("한국어 라벨 예시:")
    print("-" * 80)

    if "level_ko" in enriched.get("strength", {}):
        print(f"  강약: {enriched['strength']['level']} → {enriched['strength']['level_ko']}")

    if "primary_ko" in enriched.get("structure", {}):
        print(f"  격국: {enriched['structure']['primary']} → {enriched['structure']['primary_ko']}")

    if "confidence_ko" in enriched.get("structure", {}):
        print(f"  신뢰도: {enriched['structure']['confidence']} → {enriched['structure']['confidence_ko']}")

    if "direction_ko" in enriched.get("luck_direction", {}):
        print(f"  대운방향: {enriched['luck_direction']['direction']} → {enriched['luck_direction']['direction_ko']}")

    print()
    print("=" * 80)
    print("✅ 사주 분석 완료!")
    print("=" * 80)

if __name__ == "__main__":
    main()
