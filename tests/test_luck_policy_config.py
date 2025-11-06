
import json
from pathlib import Path

import pytest

from services.common.saju_common.engines.policy_config import (
    LuckPolicyBundle,
    LuckPolicyConfig,
    load_luck_policy_bundle,
)


@pytest.fixture(scope="module")
def drop_policy_bundle_paths():
    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / "luck_engine_v1.1.1_drop_final",
        root / "luck_engine_v1.1.1_drop_repack",
    ]
    for base in candidates:
        policy_dir = base / "policy"
        if policy_dir.exists():
            return {"base_dir": base, "policy_dir": policy_dir}
    pytest.skip("luck engine policy drop not found")


def test_load_luck_policy_from_shared_paths(drop_policy_bundle_paths):
    policy_path = drop_policy_bundle_paths["policy_dir"] / "luck_annual_policy_v1_1_1.json"
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    policy = LuckPolicyConfig.from_mapping(data)
    assert policy.policy_version.startswith("luck_annual_policy_")
    assert "relations" in policy.weights
    assert policy.policy_assumptions == tuple(data.get("policy_assumptions", []))


def test_optional_sections_are_exposed():
    data = {
        "policy_version": "luck_policy_v1.1.2",
        "weights": {},
        "hierarchy": {},
        "normalization": {},
        "options": {},
        "sect_profile": {"earth_policy": "moist_dry"},
        "policy_assumptions": ["uses_strength_based_yongxi"],
        "attribution": {"kong_mang": {"factor": 0.3}},
        "geokguk": {"detector": {"mode": "two_stage"}},
        "hap_transform_model": {"enabled": True},
        "category_overlays": {"officer": {}},
        "transformation_role_coeff": {"to_fire": {"output": 0.6}},
        "profile": {"life_stage": "mid_career"},
        "reco": {"top_k": 3},
        "alerts": {"level1_thresholds": {}},
        "ui": {"weak_frame_hint": True},
        "disclaimer": "guidance only",
    }
    cfg = LuckPolicyConfig.from_mapping(data)
    assert cfg.sect_profile == {"earth_policy": "moist_dry"}
    assert cfg.policy_assumptions == ("uses_strength_based_yongxi",)
    assert cfg.attribution == {"kong_mang": {"factor": 0.3}}
    assert cfg.geokguk == {"detector": {"mode": "two_stage"}}
    assert cfg.hap_transform_model == {"enabled": True}
    assert cfg.category_overlays == {"officer": {}}
    assert cfg.transformation_role_coeff == {"to_fire": {"output": 0.6}}
    assert cfg.profile == {"life_stage": "mid_career"}
    assert cfg.reco == {"top_k": 3}
    assert cfg.alerts == {"level1_thresholds": {}}
    assert cfg.ui == {"weak_frame_hint": True}
    assert cfg.disclaimer == "guidance only"
    assert cfg.extras == {}


def test_load_bundle_from_directory(drop_policy_bundle_paths):
    base_dir = drop_policy_bundle_paths["base_dir"]
    bundle = load_luck_policy_bundle(version="v1_1_1", base_dir=base_dir)
    assert isinstance(bundle, LuckPolicyBundle)
    assert bundle.annual.policy_version.startswith("luck_annual_policy_")
    assert bundle.monthly.policy_version.startswith("luck_monthly_policy_")
    assert bundle.daily.policy_version.startswith("luck_daily_policy_")
    if bundle.activities is not None:
        assert bundle.activities.mapping
