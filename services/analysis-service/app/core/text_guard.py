"""Text guard policy enforcement."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

# Import from common package (replaces cross-service imports)
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[6] / "services" / "common"))
from policy_loader import resolve_policy_path

# Use policy loader for flexible path resolution
POLICY_PATH = resolve_policy_path("text_guard_policy_v1.json")


@dataclass(slots=True)
class TextGuard:
    forbidden_terms: List[str]
    advice_verbs: List[str]
    must_append_when_topics: List[str]
    append_note: str

    @classmethod
    def from_file(cls, path: Path = POLICY_PATH) -> "TextGuard":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            forbidden_terms=data.get("forbidden_terms", []),
            advice_verbs=data.get("advice_verbs", []),
            must_append_when_topics=data.get("must_append_when_topics", []),
            append_note=data.get("append_note", ""),
        )

    def guard(self, text: str, topic_tags: Iterable[str]) -> str:
        filtered = text
        for term in self.forbidden_terms:
            if term in filtered:
                filtered = filtered.replace(term, "\u25cf\u25cf")
        topics = set(topic_tags)
        if (
            topics & set(self.must_append_when_topics)
            and self.append_note
            and self.append_note not in filtered
        ):
            filtered = filtered.rstrip() + " " + self.append_note
        return filtered
