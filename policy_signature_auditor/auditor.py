"""
Policy Signature Auditor - Core Logic

Handles signing, verification, and diffing of policy JSON files.
- Sign: Compute SHA-256 hash and inject into policy_signature field
- Verify: Recompute hash and compare with stored signature
- Diff: Compare canonical forms excluding signatures
"""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from . import jcs


def sign_policy(policy: Dict[str, Any], strict: bool = False) -> Tuple[str, Dict[str, Any]]:
    """
    Sign a policy by computing its SHA-256 hash.

    The policy_signature field is set to empty string before hashing,
    effectively excluding it from the hash calculation.

    Args:
        policy: Policy dictionary
        strict: If True, validate required meta fields

    Returns:
        Tuple of (sha256_hex, signed_policy)

    Raises:
        ValueError: If strict mode validation fails
    """
    if strict:
        _validate_policy_meta(policy)

    # Create copy and set policy_signature to empty string
    policy_copy = copy.deepcopy(policy)
    policy_copy["policy_signature"] = ""

    # Canonicalize and hash
    canonical_bytes = jcs.canonicalize(policy_copy)
    sha256_hash = hashlib.sha256(canonical_bytes).hexdigest()

    # Inject signature into original policy
    signed_policy = copy.deepcopy(policy)
    signed_policy["policy_signature"] = sha256_hash

    return sha256_hash, signed_policy


def verify_policy(policy: Dict[str, Any], strict: bool = False) -> Tuple[bool, str, Optional[str]]:
    """
    Verify a policy's signature.

    Args:
        policy: Policy dictionary with policy_signature field
        strict: If True, validate required meta fields

    Returns:
        Tuple of (is_valid, expected_hash, actual_hash)
        - is_valid: True if signature matches
        - expected_hash: Hash stored in policy_signature
        - actual_hash: Recomputed hash
    """
    if strict:
        _validate_policy_meta(policy)

    # Extract stored signature
    stored_signature = policy.get("policy_signature", "")
    if not stored_signature or stored_signature == "UNSIGNED":
        return False, stored_signature, None

    # Recompute hash
    expected_hash, _ = sign_policy(policy, strict=False)  # Don't re-validate

    is_valid = (stored_signature == expected_hash)
    return is_valid, expected_hash, stored_signature


def diff_policies(policy_a: Dict[str, Any], policy_b: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    Compare two policies by their canonical forms (excluding signatures).

    Args:
        policy_a: First policy
        policy_b: Second policy

    Returns:
        Tuple of (are_equal, canonical_a, canonical_b)
    """
    # Remove signatures
    a_copy = copy.deepcopy(policy_a)
    b_copy = copy.deepcopy(policy_b)
    a_copy.pop("policy_signature", None)
    b_copy.pop("policy_signature", None)

    # Canonicalize
    canonical_a = jcs.canonicalize(a_copy).decode('utf-8')
    canonical_b = jcs.canonicalize(b_copy).decode('utf-8')

    are_equal = (canonical_a == canonical_b)
    return are_equal, canonical_a, canonical_b


def _validate_policy_meta(policy: Dict[str, Any]) -> None:
    """
    Validate required meta fields in strict mode.

    Required fields:
    - policy_version
    - policy_date
    - ko_labels (must be true)
    - dependencies (list)

    Raises:
        ValueError: If validation fails
    """
    required_fields = ["policy_version", "policy_date", "ko_labels", "dependencies"]

    for field in required_fields:
        if field not in policy:
            raise ValueError(f"Missing required field in strict mode: {field}")

    # Validate ko_labels is true
    if policy.get("ko_labels") is not True:
        raise ValueError("ko_labels must be true in strict mode")

    # Validate dependencies is a list
    if not isinstance(policy.get("dependencies"), list):
        raise ValueError("dependencies must be a list in strict mode")


def sign_file(file_path: str, in_place: bool = False, write_sidecar: bool = False,
              strict: bool = False) -> Dict[str, Any]:
    """
    Sign a policy file.

    Args:
        file_path: Path to policy JSON file
        in_place: If True, update the file with signature
        write_sidecar: If True, write <file>.sha256 with hash
        strict: If True, validate meta fields

    Returns:
        Dict with keys: path, hash, signed_policy
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    # Load policy
    with open(path, 'r', encoding='utf-8') as f:
        policy = json.load(f)

    # Sign
    sha256_hash, signed_policy = sign_policy(policy, strict=strict)

    # Write in-place
    if in_place:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(signed_policy, f, ensure_ascii=False, indent=2)

    # Write sidecar
    if write_sidecar:
        sidecar_path = path.with_suffix(path.suffix + '.sha256')
        with open(sidecar_path, 'w', encoding='utf-8') as f:
            f.write(sha256_hash)

    return {
        "path": str(path),
        "hash": sha256_hash,
        "signed_policy": signed_policy
    }


def verify_file(file_path: str, strict: bool = False) -> Dict[str, Any]:
    """
    Verify a policy file's signature.

    Args:
        file_path: Path to policy JSON file
        strict: If True, validate meta fields

    Returns:
        Dict with keys: path, is_valid, expected, actual
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    # Load policy
    with open(path, 'r', encoding='utf-8') as f:
        policy = json.load(f)

    # Verify
    is_valid, expected, actual = verify_policy(policy, strict=strict)

    return {
        "path": str(path),
        "is_valid": is_valid,
        "expected": expected,
        "actual": actual
    }


def diff_files(file_a: str, file_b: str) -> Dict[str, Any]:
    """
    Compare two policy files (excluding signatures).

    Args:
        file_a: Path to first policy file
        file_b: Path to second policy file

    Returns:
        Dict with keys: are_equal, canonical_a, canonical_b
    """
    path_a = Path(file_a)
    path_b = Path(file_b)

    if not path_a.exists():
        raise FileNotFoundError(f"Policy file not found: {file_a}")
    if not path_b.exists():
        raise FileNotFoundError(f"Policy file not found: {file_b}")

    # Load policies
    with open(path_a, 'r', encoding='utf-8') as f:
        policy_a = json.load(f)
    with open(path_b, 'r', encoding='utf-8') as f:
        policy_b = json.load(f)

    # Diff
    are_equal, canonical_a, canonical_b = diff_policies(policy_a, policy_b)

    return {
        "are_equal": are_equal,
        "canonical_a": canonical_a,
        "canonical_b": canonical_b
    }
