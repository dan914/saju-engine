"""LLM validation and guard utilities for analysis responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..models import AnalysisResponse
from .recommendation import RecommendationGuard
from .text_guard import TextGuard


@dataclass(slots=True)
class LLMGuard:
    """Provide JSON validation and post-processing for LLM workflow."""

    text_guard: TextGuard
    recommendation_guard: RecommendationGuard

    @classmethod
    def default(cls) -> "LLMGuard":
        return cls(
            text_guard=TextGuard.from_file(),
            recommendation_guard=RecommendationGuard.from_file(),
        )

    def prepare_payload(self, response: AnalysisResponse) -> dict:
        """Convert response to plain dict before giving it to an LLM."""
        # Pydantic ensures structure; raising early if invalid.
        AnalysisResponse.model_validate(response.model_dump())
        return response.model_dump()

    def postprocess(
        self,
        original: AnalysisResponse,
        llm_payload: dict,
        *,
        structure_primary: str | None = None,
        topic_tags: Iterable[str] | None = None,
    ) -> AnalysisResponse:
        """Validate LLM output and enforce guards."""
        candidate = AnalysisResponse.model_validate(llm_payload)

        # Trace must remain identical (LLM은 수정 불가).
        if candidate.trace != original.trace:
            raise ValueError("LLM output modified trace metadata")

        # Text guard for trace notes (향후 확장 대비).
        notes = candidate.trace.get("notes")
        if isinstance(notes, str):
            candidate.trace["notes"] = self.text_guard.guard(notes, topic_tags or [])

        # Recommendation guard: result는 trace에 advisory 필드로 기록.
        rec = self.recommendation_guard.decide(structure_primary=structure_primary)
        candidate.trace.setdefault("recommendation", rec)
        candidate.recommendation = candidate.recommendation.__class__(**rec)

        return candidate

    def validate_llm_output(self, llm_payload: dict) -> None:
        """Standalone validation for test/CI usage."""
        AnalysisResponse.model_validate(llm_payload)
