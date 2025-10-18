"""
Tests for evidence builder (증거 수집기)
"""

import hashlib
import json
import re
from pathlib import Path

import pytest
from app.core import evidence_builder as eb

HEX64 = re.compile(r"^[0-9a-f]{64}$")
ISOZ = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


# Inline sha256_signature for tests
def sha256_signature(obj):
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def _sample_inputs_all():
    void_sig = sha256_signature({"void": "sig"})
    yuanjin_sig = sha256_signature({"yuanjin": "sig"})
    try:
        from app.core.combination_element import (
            POLICY_SIGNATURE as WUX_SIG,
        )
        from app.core.combination_element import (
            POLICY_VERSION as WUX_VER,
        )
    except Exception:
        WUX_SIG = sha256_signature({"wuxing": "sig"})
        WUX_VER = "combination_element_v1.2.0"
    return {
        "void": {
            "policy_version": "void_calc_v1.1.0",
            "policy_signature": void_sig,
            "day_index": 1,
            "xun_start": 0,
            "kong": ["戌", "亥"],
        },
        "yuanjin": {
            "policy_version": "yuanjin_v1.1.0",
            "policy_signature": yuanjin_sig,
            "present_branches": ["子", "丑", "寅", "未"],
            "hits": [["子", "未"]],
            "pair_count": 1,
        },
        "wuxing_adjust": {
            "engine_version": WUX_VER,
            "engine_signature": WUX_SIG,
            "dist": {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2},
            "trace": [
                {
                    "reason": "sanhe",
                    "target": "water",
                    "moved_ratio": 0.20,
                    "weight": 0.20,
                    "order": 1,
                    "policy_signature": WUX_SIG,
                }
            ],
        },
    }


def test_build_evidence_with_three_sections_and_order(monkeypatch):
    """Test building evidence with all 3 sections and verify sorting"""
    # 결정성 확보를 위한 timestamp freeze
    monkeypatch.setattr(eb, "_now_utc_iso", lambda: "2024-01-01T00:00:00Z")
    ev = eb.build_evidence(_sample_inputs_all())
    assert ev["evidence_version"] == eb.POLICY_VERSION
    assert HEX64.fullmatch(ev["evidence_signature"])
    assert isinstance(ev["sections"], list) and len(ev["sections"]) == 3
    # 섹션 정렬: ["void","wuxing_adjust","yuanjin"]
    types = [s["type"] for s in ev["sections"]]
    assert types == ["void", "wuxing_adjust", "yuanjin"]
    for s in ev["sections"]:
        assert HEX64.fullmatch(s["section_signature"])
        assert ISOZ.fullmatch(s["created_at"])
        # 필수 필드 존재
        for f in [
            "type",
            "engine_version",
            "engine_signature",
            "source",
            "payload",
            "created_at",
            "section_signature",
        ]:
            assert f in s


def test_optional_single_section(monkeypatch):
    """Test building evidence with only one section"""
    monkeypatch.setattr(eb, "_now_utc_iso", lambda: "2024-01-01T00:00:00Z")
    inputs = {"yuanjin": _sample_inputs_all()["yuanjin"]}
    ev = eb.build_evidence(inputs)
    assert len(ev["sections"]) == 1
    assert ev["sections"][0]["type"] == "yuanjin"
    assert HEX64.fullmatch(ev["sections"][0]["section_signature"])
    assert HEX64.fullmatch(ev["evidence_signature"])


def test_duplicate_type_add_raises(monkeypatch):
    """Test that adding duplicate section type raises ValueError"""
    monkeypatch.setattr(eb, "_now_utc_iso", lambda: "2024-01-01T00:00:00Z")
    v = _sample_inputs_all()["void"]
    ev = eb.build_evidence({"void": v})
    # 동일 타입 섹션 추가 시 오류
    dup_section = {
        "type": "void",
        "engine_version": v["policy_version"],
        "engine_signature": v["policy_signature"],
        "source": "services/analysis-service/app/core/void.py",
        "payload": {"kong": v["kong"], "day_index": v["day_index"], "xun_start": v["xun_start"]},
        "created_at": "2024-01-01T00:00:00Z",
    }
    with pytest.raises(ValueError):
        eb.add_section(ev, dup_section)


def test_schema_presence_and_patterns():
    """Test that schema file exists and has correct patterns"""
    schema_path = Path(__file__).parent.parent / "schemas" / "evidence.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["type"] == "object"
    assert set(schema["required"]) == {"evidence_version", "evidence_signature", "sections"}
    props = schema["properties"]
    assert "sections" in props and props["sections"]["items"]["type"] == "object"
    sec_props = props["sections"]["items"]["properties"]
    assert "type" in sec_props and "created_at" in sec_props and "section_signature" in sec_props
    assert "enum" in sec_props["type"]
    assert re.fullmatch(r"^[0-9a-f]{64}$", "a" * 64)
    assert re.fullmatch(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", "2024-01-01T00:00:00Z")


def test_deterministic_signature_same_inputs(monkeypatch):
    """Test that same inputs produce same signatures (idempotent)"""
    monkeypatch.setattr(eb, "_now_utc_iso", lambda: "2024-01-01T00:00:00Z")
    inputs = _sample_inputs_all()
    ev1 = eb.build_evidence(inputs)
    ev2 = eb.build_evidence(inputs)
    assert ev1["sections"] == ev2["sections"]
    assert ev1["evidence_signature"] == ev2["evidence_signature"]


def test_finalize_error_on_empty_sections():
    """Test that finalizing evidence with empty sections raises ValueError"""
    with pytest.raises(ValueError):
        eb.finalize_evidence({"evidence_version": eb.POLICY_VERSION, "sections": []})


def test_invalid_created_at_in_add_section():
    """Test that invalid created_at format raises ValueError"""
    # created_at 형식 오류
    v = _sample_inputs_all()["void"]
    ev = {"evidence_version": eb.POLICY_VERSION, "sections": []}
    bad = {
        "type": "void",
        "engine_version": v["policy_version"],
        "engine_signature": v["policy_signature"],
        "source": "services/analysis-service/app/core/void.py",
        "payload": {"kong": v["kong"], "day_index": v["day_index"], "xun_start": v["xun_start"]},
        "created_at": "2024-01-01 00:00:00Z",  # 공백 포함 → 패턴 불일치
    }
    with pytest.raises(ValueError):
        eb.add_section(ev, bad)
