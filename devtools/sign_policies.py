#!/usr/bin/env python3
"""
Signature automation for luck pillars policy dependencies.

Calculates SHA-256 signatures for all dependency policy files and injects them
into luck_pillars_policy.json.

Usage:
    python devtools/sign_policies.py
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POL_DIR = ROOT / "saju_codex_batch_all_v2_6_signed" / "policies"


def sha256(p: Path) -> str:
    """Calculate SHA-256 hash of file contents."""
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    """Calculate signatures and inject into luck pillars policy."""
    # Dependency files
    jiazi = POL_DIR / "sixty_jiazi.json"
    lifecycle = POL_DIR / "lifecycle_stages.json"
    tengods = POL_DIR / "branch_tengods_policy.json"
    luck = POL_DIR / "luck_pillars_policy.json"

    # Check if dependency files exist
    missing = []
    if not jiazi.exists():
        missing.append(str(jiazi))
    if not lifecycle.exists():
        missing.append(str(lifecycle))
    if not tengods.exists():
        missing.append(str(tengods))

    if missing:
        print("[warning] Missing dependency files:")
        for path in missing:
            print(f"  - {path}")
        print("[info] Signatures will remain as placeholders for missing files.")

    # Calculate signatures
    sigs = {
        "sixty_jiazi": sha256(jiazi) if jiazi.exists() else "<REPLACE_SIG_JIAZI>",
        "lifecycle_stages": sha256(lifecycle) if lifecycle.exists() else "<REPLACE_SIG_LIFECYCLE>",
        "branch_tengods_policy": sha256(tengods) if tengods.exists() else "<REPLACE_SIG_TENGODS>",
    }

    # Load luck policy
    pol = json.loads(luck.read_text(encoding="utf-8"))
    deps = pol.get("dependencies", {})

    # Inject signatures
    if "sixty_jiazi" in deps:
        deps["sixty_jiazi"]["signature"] = sigs["sixty_jiazi"]
    if "lifecycle_stages" in deps:
        deps["lifecycle_stages"]["signature"] = sigs["lifecycle_stages"]
    if "tengods_logic" in deps:
        deps["tengods_logic"]["signature"] = sigs["branch_tengods_policy"]

    pol["dependencies"] = deps

    # Write back
    luck.write_text(json.dumps(pol, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[ok] luck_pillars_policy.json signatures updated:")
    for name, sig in sigs.items():
        status = "✓" if not sig.startswith("<REPLACE") else "⚠"
        print(f"  {status} {name}: {sig[:16]}...")


if __name__ == "__main__":
    main()
