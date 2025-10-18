# -*- coding: utf-8 -*-
"""Centralized policy file resolution.
Search order:
  1) POLICY_DIR env var (if set)
  2) ./policy under project root (repo canonical)
  3) Legacy directories (kept for back-compat)
Usage:
  from services.common.policy_loader import resolve_policy_path, load_policy_json
  data = load_policy_json("luck_flow_policy_v1.json")
"""
import json
import os
from pathlib import Path
from typing import List

# project root = two levels up from this file: services/common/policy_loader.py → ROOT
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL = PROJECT_ROOT / "policy"

LEGACY_DIRS = [
    PROJECT_ROOT / "saju_codex_addendum_v2" / "policies",
    PROJECT_ROOT / "saju_codex_addendum_v2_1" / "policies",
    PROJECT_ROOT / "saju_codex_blueprint_v2_6_SIGNED" / "policies",
    PROJECT_ROOT / "saju_codex_v2_5_bundle" / "policies",
    PROJECT_ROOT / "saju_codex_batch_all_v2_6_signed" / "policies",
]

def search_candidates(filename: str) -> List[Path]:
    candidates = []
    env_dir = os.getenv("POLICY_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.append(CANONICAL)
    candidates.extend(LEGACY_DIRS)
    return [Path(d) / filename for d in candidates]

def resolve_policy_path(filename: str) -> Path:
    for p in search_candidates(filename):
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Policy file not found: {filename}\nSearched in:\n- " + "\n- ".join(map(str, [c.parent for c in search_candidates(filename)]))
    )

def load_policy_json(filename: str):
    path = resolve_policy_path(filename)
    return json.loads(path.read_text(encoding="utf-8"))
