from pathlib import Path
import os

# Canonical location for policy files
# __file__ is services/common/policy_loader.py
# parents[0] = services/common/
# parents[1] = services/
# parents[2] = projects/사주/ (PROJECT_ROOT)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL = PROJECT_ROOT / "policy"

# Legacy directories (searched in order after canonical location)
LEGACY_DIRS = [
    # Prioritize most recent versions first
    PROJECT_ROOT / "saju_codex_batch_all_v2_6_signed" / "policies",
    PROJECT_ROOT / "saju_codex_blueprint_v2_6_SIGNED" / "policies",
    PROJECT_ROOT / "saju_codex_v2_5_bundle" / "policies",
    PROJECT_ROOT / "saju_codex_full_v2_4" / "policies",
    PROJECT_ROOT / "saju_codex_addendum_v2_3" / "policies",
    PROJECT_ROOT / "saju_codex_addendum_v2_1" / "policies",
    PROJECT_ROOT / "saju_codex_addendum_v2" / "policies",
    PROJECT_ROOT / "saju_codex_bundle_v1" / "policy",
    PROJECT_ROOT / "saju_codex_q4_to_q10" / "policies",
]

def resolve_policy_path(filename: str) -> Path:
    env_dir = os.getenv("POLICY_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir))
    candidates += [CANONICAL] + LEGACY_DIRS
    for base in candidates:
        p = base / filename
        if p.exists():
            return p
    raise FileNotFoundError(f"Policy file not found: {filename}\nSearched in: " + "\n".join(map(str,candidates)))
