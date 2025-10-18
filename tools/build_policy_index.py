# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    out = {}
    for p in (root / "policy").glob("*.json"):
        out[p.name] = {
            "path": str(p.relative_to(root)),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
    (root / "policy_index.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
