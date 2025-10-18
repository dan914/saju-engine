"""
Unit tests for strength_grading_tiers_v1.json policy file.

Validates:
1. JSON Schema compliance
2. All 5 tiers present (극신강, 신강, 중화, 신약, 극신약)
3. Tier min scores are in descending order
4. Bin map covers all tiers
5. RFC-8785 signature integrity
"""

import hashlib
import json
from pathlib import Path

import jsonschema
from canonicaljson import encode_canonical_json


class TestStrengthGradingTiersPolicy:
    @classmethod
    def setup_class(cls):
        """Load policy and schema files once for all tests."""
        project_root = Path(__file__).parent.parent

        cls.policy_path = project_root / "policy" / "strength_grading_tiers_v1.json"
        cls.schema_path = project_root / "schema" / "strength_grading_tiers.schema.json"

        with open(cls.policy_path) as f:
            cls.policy = json.load(f)

        with open(cls.schema_path) as f:
            cls.schema = json.load(f)

    def test_schema_validation(self):
        """Test that policy conforms to JSON Schema"""
        jsonschema.validate(instance=self.policy, schema=self.schema)

    def test_all_5_tiers_present(self):
        """Test that all 5 strength tiers are present"""
        expected_tiers = {"극신강", "신강", "중화", "신약", "극신약"}
        actual_tiers = {tier["name"] for tier in self.policy["tiers"]}

        assert len(actual_tiers) == 5, f"Expected 5 tiers, got {len(actual_tiers)}"
        assert actual_tiers == expected_tiers, f"Tier names mismatch: {actual_tiers}"

    def test_tiers_in_descending_order(self):
        """Test that tiers are ordered by min score (descending)"""
        min_scores = [tier["min"] for tier in self.policy["tiers"]]

        # Should be descending: [80, 60, 40, 20, 0]
        assert min_scores == sorted(
            min_scores, reverse=True
        ), f"Tiers not in descending order: {min_scores}"

    def test_tier_min_ranges(self):
        """Test that tier min scores cover 0-100 range appropriately"""
        tiers = self.policy["tiers"]

        # First tier (극신강) should have highest min
        assert tiers[0]["min"] >= 60, f"Top tier min too low: {tiers[0]['min']}"

        # Last tier (극신약) should start at 0
        assert tiers[-1]["min"] == 0, f"Bottom tier should start at 0: {tiers[-1]['min']}"

        # All mins should be 0-100
        for tier in tiers:
            assert 0 <= tier["min"] <= 100, f"Tier {tier['name']} min out of range: {tier['min']}"

    def test_bin_map_coverage(self):
        """Test that bin_map covers all 5 tiers"""
        tier_names = {tier["name"] for tier in self.policy["tiers"]}
        bin_map_keys = set(self.policy["bin_map"].keys())

        assert (
            bin_map_keys == tier_names
        ), f"bin_map doesn't cover all tiers. Missing: {tier_names - bin_map_keys}"

    def test_bin_values_are_valid(self):
        """Test that bin_map values are one of: strong, balanced, weak"""
        valid_bins = {"strong", "balanced", "weak"}

        for tier, bin_val in self.policy["bin_map"].items():
            assert bin_val in valid_bins, f"Tier {tier} has invalid bin value: {bin_val}"

    def test_bin_mapping_logic(self):
        """Test that bin mapping follows expected strength logic"""
        # 극신강/신강 → strong
        assert self.policy["bin_map"]["극신강"] == "strong"
        assert self.policy["bin_map"]["신강"] == "strong"

        # 중화 → balanced
        assert self.policy["bin_map"]["중화"] == "balanced"

        # 신약/극신약 → weak
        assert self.policy["bin_map"]["신약"] == "weak"
        assert self.policy["bin_map"]["극신약"] == "weak"

    def test_signature_integrity(self):
        """Test RFC-8785 canonical JSON signature"""
        # Extract signature
        signature = self.policy.get("policy_signature")
        assert signature, "policy_signature field missing"
        assert len(signature) == 64, f"Signature should be 64 hex chars, got {len(signature)}"

        # Create copy without signature
        policy_copy = {k: v for k, v in self.policy.items() if k != "policy_signature"}

        # Compute canonical hash
        canonical = encode_canonical_json(policy_copy)
        computed = hashlib.sha256(canonical).hexdigest()

        assert (
            computed == signature
        ), f"Signature mismatch:\nExpected: {signature}\nComputed: {computed}"

    def test_policy_version_format(self):
        """Test that policy_version follows naming convention"""
        version = self.policy.get("policy_version")
        assert version, "policy_version field missing"
        assert version.startswith("strength_grading_tiers_v"), f"Invalid version format: {version}"

        # Extract version number
        version_num = version.replace("strength_grading_tiers_v", "")
        assert version_num.isdigit(), f"Version number should be numeric: {version_num}"
