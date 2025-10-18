#!/usr/bin/env python3
"""
Policy Signature Auditor - Basic Test Suite

Tests:
1. Sign sample policy
2. Verify signed policy
3. Detect tampering
4. Diff two policies
"""

import json
import sys
import tempfile
from pathlib import Path

# Add grandparent directory to path to import as package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from policy_signature_auditor.auditor import diff_policies, sign_policy, verify_policy


def test_sign_and_verify():
    """Test signing and verification workflow."""
    print("Test 1: Sign and verify...")

    # Load sample policy
    sample_path = Path(__file__).parent / "data" / "sample_policy.json"
    with open(sample_path, 'r', encoding='utf-8') as f:
        policy = json.load(f)

    # Sign
    sha256_hash, signed_policy = sign_policy(policy, strict=True)
    assert sha256_hash, "Hash should not be empty"
    assert signed_policy["policy_signature"] == sha256_hash
    print(f"   ✅ Signed with hash: {sha256_hash[:16]}...")

    # Verify
    is_valid, expected, actual = verify_policy(signed_policy, strict=True)
    assert is_valid, "Signature should be valid"
    assert expected == actual
    print("   ✅ Verified successfully")


def test_detect_tampering():
    """Test detection of policy tampering."""
    print("\nTest 2: Detect tampering...")

    # Load and sign policy
    sample_path = Path(__file__).parent / "data" / "sample_policy.json"
    with open(sample_path, 'r', encoding='utf-8') as f:
        policy = json.load(f)

    sha256_hash, signed_policy = sign_policy(policy, strict=True)
    print(f"   ✅ Original signature: {sha256_hash[:16]}...")

    # Tamper with policy
    tampered_policy = signed_policy.copy()
    tampered_policy["rules"][0]["action"] = "TAMPERED"

    # Verify tampered policy
    is_valid, expected, actual = verify_policy(tampered_policy, strict=False)
    assert not is_valid, "Tampered policy should fail verification"
    assert expected != actual
    print("   ✅ Tampering detected (hash mismatch)")


def test_diff_policies():
    """Test policy diffing."""
    print("\nTest 3: Diff policies...")

    # Create two policies
    policy_a = {
        "policy_version": "test_v1.0.0",
        "policy_date": "2025-10-09",
        "policy_signature": "HASH_A",
        "rules": [{"id": 1, "value": 100}]
    }

    policy_b = {
        "policy_version": "test_v1.0.0",
        "policy_date": "2025-10-09",
        "policy_signature": "HASH_B",  # Different signature
        "rules": [{"id": 1, "value": 100}]  # Same content
    }

    # Diff (should be equal despite different signatures)
    are_equal, canonical_a, canonical_b = diff_policies(policy_a, policy_b)
    assert are_equal, "Policies should be equal (excluding signatures)"
    print("   ✅ Policies are structurally equal (signatures ignored)")

    # Modify content
    policy_b["rules"][0]["value"] = 200
    are_equal, canonical_a, canonical_b = diff_policies(policy_a, policy_b)
    assert not are_equal, "Modified policies should differ"
    print("   ✅ Content difference detected")


def test_strict_mode_validation():
    """Test strict mode meta field validation."""
    print("\nTest 4: Strict mode validation...")

    # Missing required field
    invalid_policy = {
        "policy_version": "test_v1.0.0",
        # Missing policy_date
        "ko_labels": True,
        "dependencies": []
    }

    try:
        sign_policy(invalid_policy, strict=True)
        assert False, "Should raise ValueError for missing field"
    except ValueError as e:
        assert "policy_date" in str(e)
        print(f"   ✅ Missing field detected: {e}")

    # Invalid ko_labels
    invalid_policy = {
        "policy_version": "test_v1.0.0",
        "policy_date": "2025-10-09",
        "ko_labels": False,  # Should be true
        "dependencies": []
    }

    try:
        sign_policy(invalid_policy, strict=True)
        assert False, "Should raise ValueError for ko_labels=false"
    except ValueError as e:
        assert "ko_labels" in str(e)
        print(f"   ✅ Invalid ko_labels detected: {e}")


def test_file_operations():
    """Test file-based operations."""
    print("\nTest 5: File operations...")

    from policy_signature_auditor.auditor import sign_file, verify_file

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        policy = {
            "policy_version": "test_v1.0.0",
            "policy_date": "2025-10-09",
            "policy_signature": "UNSIGNED",
            "ko_labels": True,
            "dependencies": []
        }
        json.dump(policy, f, indent=2)
        temp_path = f.name

    try:
        # Sign in-place
        result = sign_file(temp_path, in_place=True, strict=True)
        assert result['hash'], "Hash should be generated"
        print(f"   ✅ File signed: {result['hash'][:16]}...")

        # Verify
        result = verify_file(temp_path, strict=True)
        assert result['is_valid'], "File signature should be valid"
        print("   ✅ File verified")

    finally:
        # Cleanup
        Path(temp_path).unlink()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Policy Signature Auditor - Test Suite")
    print("=" * 60)

    try:
        test_sign_and_verify()
        test_detect_tampering()
        test_diff_policies()
        test_strict_mode_validation()
        test_file_operations()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())
