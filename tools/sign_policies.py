#!/usr/bin/env python3
"""
Sign policy files with RFC-8785 canonical JSON signatures.

This script:
1. Reads each policy file
2. Removes any existing signature field
3. Canonicalizes the JSON using RFC-8785
4. Computes SHA-256 hash
5. Adds the signature back to the policy
6. Writes the updated policy

Usage:
    python tools/sign_policies.py
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

try:
    from canonicaljson import encode_canonical_json

    HAS_CANONICAL = True
except ImportError:
    HAS_CANONICAL = False
    print("WARNING: canonicaljson not installed. Install with: pip install canonicaljson")
    print("Falling back to simple JSON serialization (not RFC-8785 compliant)")


def sign_policy_rfc8785(policy_data: Dict[str, Any]) -> str:
    """
    Sign policy using RFC-8785 canonical JSON.

    Args:
        policy_data: Policy dict (will be copied, not modified)

    Returns:
        SHA-256 hex digest
    """
    # Remove signature fields if present
    data_copy = {
        k: v
        for k, v in policy_data.items()
        if k not in ("policy_signature", "signature", "signatures")
    }

    if HAS_CANONICAL:
        # RFC-8785 compliant canonicalization
        canonical = encode_canonical_json(data_copy)
    else:
        # Fallback: deterministic JSON (not fully RFC-8785 compliant)
        canonical = json.dumps(
            data_copy, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    # Compute SHA-256
    sha256 = hashlib.sha256(canonical).hexdigest()
    return sha256


def sign_policy_file(policy_path: Path, signature_field: str = "policy_signature") -> bool:
    """
    Sign a single policy file.

    Args:
        policy_path: Path to policy JSON file
        signature_field: Name of signature field to use

    Returns:
        True if signed successfully, False otherwise
    """
    try:
        # Read policy
        with policy_path.open("r", encoding="utf-8") as f:
            policy = json.load(f)

        # Check if already has placeholder
        old_sig = policy.get(signature_field, policy.get("signature"))

        # Compute signature
        signature = sign_policy_rfc8785(policy)

        # Update policy
        policy[signature_field] = signature

        # Write back
        with policy_path.open("w", encoding="utf-8") as f:
            json.dump(policy, f, indent=2, ensure_ascii=False)
            f.write("\n")  # Add trailing newline

        # Report
        if old_sig == "<TO_BE_FILLED_BY_PSA>":
            print(f"✅ Signed (was placeholder): {policy_path.name}")
        elif old_sig and old_sig != signature:
            print(f"🔄 Re-signed (signature changed): {policy_path.name}")
        elif not old_sig:
            print(f"✅ Signed (new signature): {policy_path.name}")
        else:
            print(f"✓  Already signed correctly: {policy_path.name}")

        print(f"   SHA-256: {signature}")
        return True

    except Exception as e:
        print(f"❌ Error signing {policy_path.name}: {e}")
        return False


def main():
    """Sign all policy files in policy/ directory."""
    repo_root = Path(__file__).resolve().parents[1]
    policy_dir = repo_root / "policy"

    if not policy_dir.exists():
        print(f"❌ Policy directory not found: {policy_dir}")
        return 1

    print("=" * 60)
    print("Policy File Signing Tool")
    print("=" * 60)
    print()

    if not HAS_CANONICAL:
        print("⚠️  WARNING: Running without canonicaljson library")
        print("   Install with: pip install canonicaljson")
        print("   Signatures will NOT be RFC-8785 compliant!")
        print()
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            return 1
        print()

    # Find all JSON files in policy/
    policy_files = sorted(policy_dir.glob("*.json"))

    if not policy_files:
        print(f"❌ No policy files found in {policy_dir}")
        return 1

    print(f"Found {len(policy_files)} policy files:\n")

    success_count = 0
    for policy_file in policy_files:
        if sign_policy_file(policy_file):
            success_count += 1
        print()

    print("=" * 60)
    print(f"✅ Successfully signed {success_count}/{len(policy_files)} policy files")

    if success_count < len(policy_files):
        print(f"❌ Failed to sign {len(policy_files) - success_count} files")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
