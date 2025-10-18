"""
Unit tests for seasons_wang_map_v2.json policy file.

Validates:
1. JSON Schema compliance
2. All 12 earthly branches present
3. All 5 elements for each branch
4. Wang states are valid (旺, 相, 休, 囚, 死)
5. RFC-8785 signature integrity
"""
import hashlib
import json
from pathlib import Path

import jsonschema
from canonicaljson import encode_canonical_json


class TestSeasonsWangMapPolicy:
    @classmethod
    def setup_class(cls):
        """Load policy and schema files once for all tests."""
        project_root = Path(__file__).parent.parent

        cls.policy_path = project_root / "policy" / "seasons_wang_map_v2.json"
        cls.schema_path = project_root / "schema" / "seasons_wang_map.schema.json"

        with open(cls.policy_path) as f:
            cls.policy = json.load(f)

        with open(cls.schema_path) as f:
            cls.schema = json.load(f)

    def test_schema_validation(self):
        """Test that policy conforms to JSON Schema"""
        jsonschema.validate(instance=self.policy, schema=self.schema)

    def test_all_12_branches_present(self):
        """Test that all 12 earthly branches are present in by_branch"""
        expected_branches = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
        actual_branches = list(self.policy["by_branch"].keys())

        assert len(actual_branches) == 12, f"Expected 12 branches, got {len(actual_branches)}"

        for branch in expected_branches:
            assert branch in actual_branches, f"Missing branch: {branch}"

    def test_all_elements_in_each_branch(self):
        """Test that each branch has all 5 elements"""
        expected_elements = ["wood", "fire", "earth", "metal", "water"]

        for branch, elements in self.policy["by_branch"].items():
            actual_elements = list(elements.keys())
            assert len(actual_elements) == 5, f"Branch {branch} has {len(actual_elements)} elements, expected 5"

            for element in expected_elements:
                assert element in actual_elements, f"Branch {branch} missing element: {element}"

    def test_wang_states_are_valid(self):
        """Test that all Wang states are one of the 5 valid values"""
        valid_states = {"旺", "相", "休", "囚", "死"}

        for branch, elements in self.policy["by_branch"].items():
            for element, state in elements.items():
                assert state in valid_states, f"Branch {branch}, element {element}: invalid state '{state}'"

    def test_stages_array(self):
        """Test that stages array contains all 5 Wang states"""
        expected_stages = ["旺", "相", "休", "囚", "死"]
        actual_stages = self.policy["stages"]

        assert len(actual_stages) == 5, f"Expected 5 stages, got {len(actual_stages)}"
        assert actual_stages == expected_stages, f"Stages mismatch: {actual_stages}"

    def test_score_map_coverage(self):
        """Test that score_map has entries for all 5 Wang states"""
        valid_states = {"旺", "相", "休", "囚", "死"}
        score_map_keys = set(self.policy["score_map"].keys())

        assert score_map_keys == valid_states, f"score_map keys mismatch: {score_map_keys}"

        # Verify all scores are integers
        for state, score in self.policy["score_map"].items():
            assert isinstance(score, int), f"Score for {state} is not an integer: {score}"

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
        assert version.startswith("seasons_wang_map_v"), f"Invalid version format: {version}"

        # Extract version number
        version_num = version.replace("seasons_wang_map_v", "")
        assert version_num.isdigit(), f"Version number should be numeric: {version_num}"
