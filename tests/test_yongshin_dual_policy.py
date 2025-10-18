"""
Unit tests for yongshin_dual_policy_v1.json policy file.

Validates:
1. JSON Schema compliance
2. All 4 seasons in climate_rules (봄, 여름, 가을, 겨울)
3. All 3 bins in bin_base_weights (weak, balanced, strong)
4. All 5 ten god types in each bin
5. Distribution parameters are valid floats
6. RFC-8785 signature integrity
"""
import hashlib
import json
from pathlib import Path

import jsonschema
from canonicaljson import encode_canonical_json


class TestYongshinDualPolicy:
    @classmethod
    def setup_class(cls):
        """Load policy and schema files once for all tests."""
        project_root = Path(__file__).parent.parent

        cls.policy_path = project_root / "policy" / "yongshin_dual_policy_v1.json"
        cls.schema_path = project_root / "schema" / "yongshin_dual_policy.schema.json"

        with open(cls.policy_path) as f:
            cls.policy = json.load(f)

        with open(cls.schema_path) as f:
            cls.schema = json.load(f)

    def test_schema_validation(self):
        """Test that policy conforms to JSON Schema"""
        jsonschema.validate(instance=self.policy, schema=self.schema)

    def test_all_4_seasons_present(self):
        """Test that all 4 seasons are in climate_rules"""
        expected_seasons = {"봄", "여름", "가을", "겨울"}
        actual_seasons = set(self.policy["climate_rules"].keys())

        assert actual_seasons == expected_seasons, \
            f"Season mismatch. Expected: {expected_seasons}, Got: {actual_seasons}"

    def test_climate_candidates_are_valid(self):
        """Test that climate candidates are valid elements"""
        valid_elements = {"목", "화", "토", "금", "수"}

        for season, rule in self.policy["climate_rules"].items():
            candidates = rule.get("candidates", [])
            assert len(candidates) > 0, f"Season {season} has no candidates"

            for candidate in candidates:
                assert candidate in valid_elements, \
                    f"Season {season}: invalid candidate '{candidate}'"

    def test_climate_weights_are_valid(self):
        """Test that primary_weight values are in [0, 1] range"""
        for season, rule in self.policy["climate_rules"].items():
            weight = rule.get("primary_weight")
            assert weight is not None, f"Season {season} missing primary_weight"
            assert 0 <= weight <= 1, \
                f"Season {season}: primary_weight {weight} out of range [0, 1]"

    def test_all_3_bins_present(self):
        """Test that all 3 strength bins are in bin_base_weights"""
        expected_bins = {"weak", "balanced", "strong"}
        actual_bins = set(self.policy["bin_base_weights"].keys())

        assert actual_bins == expected_bins, \
            f"Bin mismatch. Expected: {expected_bins}, Got: {actual_bins}"

    def test_all_tengod_types_in_each_bin(self):
        """Test that each bin has all 5 ten god types"""
        expected_types = {"resource", "companion", "output", "wealth", "official"}

        for bin_name, weights in self.policy["bin_base_weights"].items():
            actual_types = set(weights.keys())
            assert actual_types == expected_types, \
                f"Bin {bin_name}: type mismatch. Expected: {expected_types}, Got: {actual_types}"

    def test_tengod_weights_are_valid(self):
        """Test that all ten god weights are in [0, 1] range"""
        for bin_name, weights in self.policy["bin_base_weights"].items():
            for tengod_type, weight in weights.items():
                assert 0 <= weight <= 1, \
                    f"Bin {bin_name}, type {tengod_type}: weight {weight} out of range [0, 1]"

    def test_bin_weight_logic(self):
        """Test that bin weights follow expected yongshin logic"""
        weak = self.policy["bin_base_weights"]["weak"]
        strong = self.policy["bin_base_weights"]["strong"]

        # Weak should favor resource/companion (support)
        assert weak["resource"] > weak["output"], \
            "Weak bin should favor resource over output"
        assert weak["resource"] > weak["wealth"], \
            "Weak bin should favor resource over wealth"

        # Strong should favor output/wealth (drain)
        assert strong["output"] > strong["resource"], \
            "Strong bin should favor output over resource"
        assert strong["wealth"] > strong["resource"], \
            "Strong bin should favor wealth over resource"

    def test_distribution_parameters(self):
        """Test that distribution parameters are valid"""
        dist = self.policy["distribution"]

        # Check all required fields
        assert "target_ratio" in dist
        assert "deficit_gain_max" in dist
        assert "excess_penalty_max" in dist

        # Check ranges
        assert 0 <= dist["target_ratio"] <= 1, \
            f"target_ratio out of range: {dist['target_ratio']}"
        assert 0 <= dist["deficit_gain_max"] <= 1, \
            f"deficit_gain_max out of range: {dist['deficit_gain_max']}"
        assert 0 <= dist["excess_penalty_max"] <= 1, \
            f"excess_penalty_max out of range: {dist['excess_penalty_max']}"

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

        assert computed == signature, f"Signature mismatch:\nExpected: {signature}\nComputed: {computed}"

    def test_policy_version_format(self):
        """Test that policy_version follows naming convention"""
        version = self.policy.get("policy_version")
        assert version, "policy_version field missing"
        assert version.startswith("yongshin_dual_v"), f"Invalid version format: {version}"

        # Extract version number
        version_num = version.replace("yongshin_dual_v", "")
        assert version_num.isdigit(), f"Version number should be numeric: {version_num}"
