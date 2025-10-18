# -*- coding: utf-8 -*-
"""
Test Ten Gods Engine v1.0

Validates:
- Schema compliance
- Ten Gods calculation logic
- Summary aggregation
- Dominant/missing detection
"""
import json
from pathlib import Path

from app.core.ten_gods import TenGodsCalculator
from jsonschema import validate

BASE = Path(__file__).resolve().parents[3]
POLICY_PATH = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "branch_tengods_policy.json"
SCHEMA_PATH = BASE / "schema" / "ten_gods.schema.json"


def load_policy() -> dict:
    """Load branch_tengods_policy."""
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def load_schema() -> dict:
    """Load ten_gods schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_validation():
    """Ten Gods output must pass schema validation."""
    policy = load_policy()
    schema = load_schema()

    pillars = {
        "year":  {"stem": "庚", "branch": "辰"},
        "month": {"stem": "乙", "branch": "酉"},
        "day":   {"stem": "乙", "branch": "亥"},
        "hour":  {"stem": "辛", "branch": "巳"}
    }

    engine = TenGodsCalculator(policy, output_policy_version="ten_gods_v1.0")
    result = engine.evaluate(pillars)

    # Should not raise
    validate(instance=result, schema=schema)


def test_sample_chart_output():
    """Test known chart (2000-09-14) output."""
    policy = load_policy()

    pillars = {
        "year":  {"stem": "庚", "branch": "辰"},
        "month": {"stem": "乙", "branch": "酉"},
        "day":   {"stem": "乙", "branch": "亥"},
        "hour":  {"stem": "辛", "branch": "巳"}
    }

    engine = TenGodsCalculator(policy, output_policy_version="ten_gods_v1.0")
    out = engine.evaluate(pillars)

    # Day stem should be 比肩 (self)
    assert out["by_pillar"]["day"]["vs_day"] == "比肩"

    # Year stem 庚 vs day stem 乙 (木) -> 金克木 -> 正官
    assert out["by_pillar"]["year"]["vs_day"] == "正官"

    # Hour stem 辛 vs day stem 乙 (木) -> 金克木 -> 七殺
    assert out["by_pillar"]["hour"]["vs_day"] == "七殺"

    # Summary should have counts
    assert "正官" in out["summary"]
    assert out["summary"]["正官"] >= 2

    # Dominant should be highest count
    assert len(out["dominant"]) > 0
    assert "比肩" in out["dominant"]  # Should be dominant (3 count)

    # Missing should list unused gods
    assert len(out["missing"]) > 0
    assert "食神" in out["missing"]


def test_day_stem_flip_changes_calculation():
    """Changing day stem should change Ten Gods calculation."""
    policy = load_policy()

    pillars_A = {
        "year":  {"stem": "庚", "branch": "辰"},
        "month": {"stem": "乙", "branch": "酉"},
        "day":   {"stem": "乙", "branch": "亥"},
        "hour":  {"stem": "辛", "branch": "巳"}
    }

    pillars_B = {
        "year":  {"stem": "庚", "branch": "辰"},
        "month": {"stem": "乙", "branch": "酉"},
        "day":   {"stem": "甲", "branch": "亥"},  # Changed to 甲
        "hour":  {"stem": "辛", "branch": "巳"}
    }

    engine = TenGodsCalculator(policy)
    out_A = engine.evaluate(pillars_A)
    out_B = engine.evaluate(pillars_B)

    # Results should differ
    assert out_A["summary"] != out_B["summary"]
    assert out_A["dominant"] != out_B["dominant"]


def test_hidden_stems_counted():
    """Hidden stems should be included in summary."""
    policy = load_policy()

    pillars = {
        "year":  {"stem": "庚", "branch": "辰"},
        "month": {"stem": "乙", "branch": "酉"},
        "day":   {"stem": "乙", "branch": "亥"},
        "hour":  {"stem": "辛", "branch": "巳"}
    }

    engine = TenGodsCalculator(policy)
    out = engine.evaluate(pillars)

    # Year branch 辰 has hidden stems: 戊(primary), 乙(secondary), 癸(tertiary)
    year_hidden = out["by_pillar"]["year"]["hidden"]
    assert "戊" in year_hidden
    assert "乙" in year_hidden
    assert "癸" in year_hidden

    # These should contribute to summary
    total_count = sum(out["summary"].values())
    assert total_count > 4  # More than just 4 stems


def test_signature_deterministic():
    """Policy signature should be deterministic."""
    policy = load_policy()

    pillars = {
        "year":  {"stem": "庚", "branch": "辰"},
        "month": {"stem": "乙", "branch": "酉"},
        "day":   {"stem": "乙", "branch": "亥"},
        "hour":  {"stem": "辛", "branch": "巳"}
    }

    engine = TenGodsCalculator(policy)
    out1 = engine.evaluate(pillars)
    out2 = engine.evaluate(pillars)

    # Same input should produce same signature
    assert out1["policy_signature"] == out2["policy_signature"]
    assert len(out1["policy_signature"]) == 64  # SHA-256 hex
