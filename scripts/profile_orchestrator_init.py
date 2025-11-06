#!/usr/bin/env python3
"""Profile SajuOrchestrator initialization to identify slow components.

This script instruments each engine initialization in SajuOrchestrator.__init__()
to measure which components are taking the most time.
"""
import sys
import time
from pathlib import Path

# Add services to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "services" / "analysis-service"))
sys.path.insert(0, str(repo_root / "services" / "common"))


def profile_init():
    """Profile each component initialization in SajuOrchestrator."""
    print("\n" + "="*80)
    print("🔍 SajuOrchestrator Initialization Profile")
    print("="*80 + "\n")

    timings = []

    def time_op(name, func):
        start = time.perf_counter()
        print(f"⏱️  Loading: {name}...", end=" ", flush=True)
        try:
            result = func()
            elapsed = time.perf_counter() - start
            print(f"✅ {elapsed:.3f}s")
            timings.append((name, elapsed))
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            print(f"❌ {elapsed:.3f}s - ERROR: {e}")
            timings.append((name, elapsed, str(e)))
            raise

    # Import dependencies
    print("Importing dependencies...")
    from services.common.policy_loader import load_policy_json
    from app.core.strength_v2 import StrengthEvaluator
    from app.core.relations import RelationTransformer
    from app.core.relation_weight import RelationWeightEvaluator
    from app.core.relations_extras import RelationAnalyzer
    from app.core.climate import ClimateEvaluator
    from app.core.yongshin_selector_v2 import YongshinSelector
    from app.core.luck import ShenshaCatalog
    from app.core.ten_gods import TenGodsCalculator
    from app.core.luck_seed_builder import LuckSeedBuilder
    from app.core.twelve_stages import TwelveStagesCalculator
    from app.core.luck_pillars import LuckCalculator
    from app.core.climate_advice import ClimateAdvice
    from app.core.luck_flow import LuckFlow
    from app.core.gyeokguk_classifier import GyeokgukClassifier
    from app.core.pattern_profiler import PatternProfiler
    from app.core.engine_summaries import EngineSummariesBuilder
    from app.core.korean_enricher import KoreanLabelEnricher
    from app.core.school import SchoolProfileManager
    from app.core.recommendation import RecommendationGuard
    from app.core.llm_guard import LLMGuard
    from app.core.text_guard import TextGuard
    from services.common.saju_common import FileSolarTermLoader, BasicTimeResolver
    from services.common.saju_common.engines import (
        AnnualLuckCalculator,
        DailyLuckCalculator,
        MonthlyLuckCalculator,
    )
    print("✅ Imports complete\n")

    print("-"*80)
    print("Core Engines:")
    print("-"*80)

    strength = time_op("StrengthEvaluator", lambda: StrengthEvaluator())
    relations = time_op("RelationTransformer", lambda: RelationTransformer.from_file())
    relation_weight = time_op("RelationWeightEvaluator", lambda: RelationWeightEvaluator())
    relations_analyzer = time_op("RelationAnalyzer", lambda: RelationAnalyzer())
    climate = time_op("ClimateEvaluator", lambda: ClimateEvaluator.from_file())
    yongshin = time_op("YongshinSelector", lambda: YongshinSelector())
    shensha = time_op("ShenshaCatalog", lambda: ShenshaCatalog())

    print("\n" + "-"*80)
    print("Ten Gods & Lifecycle:")
    print("-"*80)

    ten_gods_policy = time_op("load_policy: branch_tengods_policy.json",
                               lambda: load_policy_json("branch_tengods_policy.json"))
    ten_gods = time_op("TenGodsCalculator",
                       lambda: TenGodsCalculator(ten_gods_policy, output_policy_version="ten_gods_v1.0"))
    luck_seed_builder = time_op("LuckSeedBuilder", lambda: LuckSeedBuilder(ten_gods))
    annual_luck = time_op("AnnualLuckCalculator", lambda: AnnualLuckCalculator())
    monthly_luck = time_op("MonthlyLuckCalculator", lambda: MonthlyLuckCalculator())
    daily_luck = time_op("DailyLuckCalculator", lambda: DailyLuckCalculator())

    lifecycle_policy = time_op("load_policy: lifecycle_stages.json",
                                lambda: load_policy_json("lifecycle_stages.json"))
    twelve_stages = time_op("TwelveStagesCalculator",
                            lambda: TwelveStagesCalculator(lifecycle_policy,
                                                           output_policy_version="twelve_stages_v1.0"))

    print("\n" + "-"*80)
    print("Luck Pillars:")
    print("-"*80)

    luck_pillars_policy = time_op("load_policy: luck_pillars_policy.json",
                                   lambda: load_policy_json("luck_pillars_policy.json"))
    luck = time_op("LuckCalculator", lambda: LuckCalculator(luck_pillars_policy))

    print("\n" + "-"*80)
    print("Stage-3 MVP Engines:")
    print("-"*80)

    climate_advice = time_op("ClimateAdvice", lambda: ClimateAdvice())
    luck_flow = time_op("LuckFlow", lambda: LuckFlow())
    gyeokguk = time_op("GyeokgukClassifier", lambda: GyeokgukClassifier())
    pattern = time_op("PatternProfiler", lambda: PatternProfiler())

    print("\n" + "-"*80)
    print("Post-Processing Engines:")
    print("-"*80)

    summaries = time_op("EngineSummariesBuilder", lambda: EngineSummariesBuilder())
    korean = time_op("KoreanLabelEnricher", lambda: KoreanLabelEnricher.from_files())
    school = time_op("SchoolProfileManager", lambda: SchoolProfileManager.load())
    reco = time_op("RecommendationGuard", lambda: RecommendationGuard.from_file())
    llm_guard = time_op("LLMGuard", lambda: LLMGuard.default())
    text_guard = time_op("TextGuard", lambda: TextGuard.from_file())

    print("\n" + "-"*80)
    print("Utilities:")
    print("-"*80)

    DATA_PATH = repo_root / "data"
    solar_term_loader = time_op("FileSolarTermLoader", lambda: FileSolarTermLoader(DATA_PATH))
    time_resolver = time_op("BasicTimeResolver", lambda: BasicTimeResolver())

    # Summary
    print("\n" + "="*80)
    print("📊 Timing Summary")
    print("="*80 + "\n")

    # Sort by duration
    sorted_timings = sorted([(n, t) for n, t, *_ in timings if isinstance(t, (int, float))],
                            key=lambda x: x[1], reverse=True)

    total_time = sum(t for _, t in sorted_timings)

    print(f"{'Component':<45} {'Time':>10} {'%':>8}")
    print("-"*80)
    for name, duration in sorted_timings:
        pct = (duration / total_time * 100) if total_time > 0 else 0
        print(f"{name:<45} {duration:>8.3f}s {pct:>7.1f}%")

    print("="*80)
    print(f"{'TOTAL':<45} {total_time:>8.3f}s {'100.0%':>8}")
    print("="*80 + "\n")

    # Highlight slow components (>50ms)
    slow = [(n, t) for n, t in sorted_timings if t > 0.050]
    if slow:
        print("⚠️  Slow components (>50ms):")
        for name, duration in slow:
            print(f"   • {name}: {duration:.3f}s")
        print()


if __name__ == "__main__":
    try:
        profile_init()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
