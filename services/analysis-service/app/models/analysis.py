"""Data models for ten gods / relations / strength analysis."""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class PillarInput(BaseModel):
    """Simple representation of a pillar used for analysis."""

    pillar: str
    stem: str | None = None
    branch: str | None = None


class AnalysisOptions(BaseModel):
    """Optional toggles (placeholder for future customization)."""

    include_trace: bool = True


class TenGodsResult(BaseModel):
    """Mapping of stem relationships (placeholder structure)."""

    summary: dict[str, str]


class RelationsResult(BaseModel):
    """Grouped relations (六合/三合/冲/害/破/刑)."""

    he6: List[List[str]]
    sanhe: List[List[str]]
    chong: List[List[str]]
    hai: List[List[str]]
    po: List[List[str]]
    xing: List[List[str]]


class RelationsExtras(BaseModel):
    priority_hit: str | None = None
    transform_to: str | None = None
    boosts: List[Dict[str, str]] = Field(default_factory=list)
    extras: dict[str, object] = Field(default_factory=dict)


class StrengthResult(BaseModel):
    """Qualitative strength evaluation."""

    level: str
    basis: dict[str, str]


class StrengthDetails(BaseModel):
    month_state: int
    branch_root: int
    stem_visible: int
    combo_clash: int
    season_adjust: int
    month_stem_effect: int
    wealth_location_bonus_total: float = 0.0
    wealth_location_hits: List[Dict[str, object]] = Field(default_factory=list)
    total: float
    grade_code: str
    grade: str
    seal_validity: Dict[str, object] = Field(default_factory=dict)


class StructureResultModel(BaseModel):
    primary: str | None
    confidence: str
    candidates: List[Dict[str, object]]


class LuckResult(BaseModel):
    prev_term: str | None
    next_term: str | None
    interval_days: float | None
    days_from_prev: float | None
    start_age: float | None


class LuckDirectionResult(BaseModel):
    direction: str | None
    method: str | None
    sex_at_birth: str | None


class ShenshaResult(BaseModel):
    enabled: bool
    list: List[object]


class SchoolProfileResult(BaseModel):
    id: str
    notes: str | None = None


class RecommendationResult(BaseModel):
    enabled: bool
    action: str
    copy: str | None = None


class AnalysisRequest(BaseModel):
    """Input payload for analysis service."""

    pillars: dict[str, PillarInput]
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)


class AnalysisResponse(BaseModel):
    """Analysis output aligned with requirements."""

    ten_gods: TenGodsResult
    relations: RelationsResult
    relation_extras: RelationsExtras
    strength: StrengthResult
    strength_details: StrengthDetails
    structure: StructureResultModel
    luck: LuckResult
    luck_direction: LuckDirectionResult
    shensha: ShenshaResult
    school_profile: SchoolProfileResult
    recommendation: RecommendationResult
    trace: dict[str, object]
