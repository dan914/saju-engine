#!/usr/bin/env python3
"""
Fix ci_checks in relation_policy.json to match schema requirements.
- Rename 'id' to 'check_id'
- Remove 'severity' and 'auto_fix' fields
- Add 'assertion' field based on description
"""

import json
from pathlib import Path


def transform_ci_checks(ci_checks):
    """Transform ci_checks to match schema."""
    transformed = []
    for check in ci_checks:
        new_check = {
            "check_id": check["id"],
            "description": check["description"],
            "assertion": check["description"],  # Use description as assertion
        }
        transformed.append(new_check)
    return transformed


def main():
    policy_path = Path(
        "/Users/yujumyeong/coding/ projects/사주/saju_codex_batch_all_v2_6_signed/policies/relation_policy.json"
    )

    # Load policy
    with open(policy_path) as f:
        policy = json.load(f)

    print(f"Original ci_checks count: {len(policy['ci_checks'])}")

    # Transform ci_checks
    policy["ci_checks"] = transform_ci_checks(policy["ci_checks"])

    print(f"Transformed ci_checks count: {len(policy['ci_checks'])}")

    # Save updated policy
    with open(policy_path, "w") as f:
        json.dump(policy, f, ensure_ascii=False, indent=2)

    print(f"✅ Updated {policy_path}")

    # Show first transformed check
    print("\nSample transformed check:")
    print(json.dumps(policy["ci_checks"][0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
