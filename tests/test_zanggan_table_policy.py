"""
Unit tests for zanggan_table.json policy file.

Validates:
1. JSON Schema compliance
2. All 12 earthly branches present
3. Each branch has main/sub/minor structure
4. All stems are valid heavenly stems (甲乙丙丁戊己庚辛壬癸)
5. Array sizes: sub (0-2), minor (0-1)
6. RFC-8785 signature integrity
"""
import hashlib
import json
from pathlib import Path

import jsonschema
from canonicaljson import encode_canonical_json


class TestZangganTablePolicy:
    @classmethod
    def setup_class(cls):
        """Load policy and schema files once for all tests."""
        project_root = Path(__file__).parent.parent

        cls.policy_path = project_root / "policy" / "zanggan_table.json"
        cls.schema_path = project_root / "schema" / "zanggan_table.schema.json"

        with open(cls.policy_path) as f:
            cls.policy = json.load(f)

        with open(cls.schema_path) as f:
            cls.schema = json.load(f)

        cls.valid_stems = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}

    def test_schema_validation(self):
        """Test that policy conforms to JSON Schema"""
        jsonschema.validate(instance=self.policy, schema=self.schema)

    def test_all_12_branches_present(self):
        """Test that all 12 earthly branches are present"""
        expected_branches = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}
        actual_branches = set(self.policy["by_branch"].keys())

        assert len(actual_branches) == 12, f"Expected 12 branches, got {len(actual_branches)}"
        assert actual_branches == expected_branches, \
            f"Branch mismatch. Missing: {expected_branches - actual_branches}"

    def test_each_branch_has_required_fields(self):
        """Test that each branch has main, sub, minor fields"""
        for branch, entry in self.policy["by_branch"].items():
            assert "main" in entry, f"Branch {branch} missing 'main' field"
            assert "sub" in entry, f"Branch {branch} missing 'sub' field"
            assert "minor" in entry, f"Branch {branch} missing 'minor' field"

    def test_main_stem_is_valid(self):
        """Test that main stem is a valid heavenly stem"""
        for branch, entry in self.policy["by_branch"].items():
            main = entry["main"]
            assert main in self.valid_stems, \
                f"Branch {branch}: invalid main stem '{main}'"

    def test_sub_stems_are_valid(self):
        """Test that sub stems are valid and within size limit"""
        for branch, entry in self.policy["by_branch"].items():
            sub = entry["sub"]
            assert isinstance(sub, list), f"Branch {branch}: sub should be array"
            assert len(sub) <= 2, f"Branch {branch}: sub has {len(sub)} items, max 2"

            for stem in sub:
                assert stem in self.valid_stems, \
                    f"Branch {branch}: invalid sub stem '{stem}'"

    def test_minor_stems_are_valid(self):
        """Test that minor stems are valid and within size limit"""
        for branch, entry in self.policy["by_branch"].items():
            minor = entry["minor"]
            assert isinstance(minor, list), f"Branch {branch}: minor should be array"
            assert len(minor) <= 1, f"Branch {branch}: minor has {len(minor)} items, max 1"

            for stem in minor:
                assert stem in self.valid_stems, \
                    f"Branch {branch}: invalid minor stem '{stem}'"

    def test_no_duplicate_stems_within_branch(self):
        """Test that each branch doesn't have duplicate stems across main/sub/minor"""
        for branch, entry in self.policy["by_branch"].items():
            all_stems = [entry["main"]] + entry["sub"] + entry["minor"]
            unique_stems = set(all_stems)

            assert len(all_stems) == len(unique_stems), \
                f"Branch {branch} has duplicate stems: {all_stems}"

    def test_known_zanggan_examples(self):
        """Test known zanggan mappings from traditional theory"""
        # 子 (Water) should have 癸 as main
        assert self.policy["by_branch"]["子"]["main"] == "癸"

        # 午 (Fire) should have 丁 as main
        assert self.policy["by_branch"]["午"]["main"] == "丁"

        # 卯 (Wood) should have 乙 as main
        assert self.policy["by_branch"]["卯"]["main"] == "乙"

        # 酉 (Metal) should have 辛 as main
        assert self.policy["by_branch"]["酉"]["main"] == "辛"

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
        assert version.startswith("zanggan_table_v"), f"Invalid version format: {version}"

        # Extract version number
        version_num = version.replace("zanggan_table_v", "")
        assert version_num.isdigit(), f"Version number should be numeric: {version_num}"
