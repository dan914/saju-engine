"""Data models for analysis pipeline responses."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class PillarInput(BaseModel):
    """Simple representation of a pillar used for analysis."""

    pillar: str
    stem: str | None = None
    branch: str | None = None


class AnalysisOptions(BaseModel):
    """Optional toggles and birth context for analysis."""

    include_trace: bool = True
    birth_dt: str | None = None  # ISO8601 datetime string
    gender: str | None = None  # "M" or "F"
    timezone: str = "Asia/Seoul"  # IANA timezone


class TenGodsPillar(BaseModel):
    stem: str | None = None
    branch: str | None = None
    vs_day: str | None = None
    hidden: Dict[str, str] = Field(default_factory=dict)


class TenGodsResult(BaseModel):
    policy_version: str | None = None
    policy_signature: str | None = None
    by_pillar: Dict[str, TenGodsPillar] = Field(default_factory=dict)
    summary: Dict[str, int] = Field(default_factory=dict)
    dominant: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)


class TwelveStagesPillar(BaseModel):
    stem: str | None = None
    branch: str | None = None
    stage_zh: str | None = None
    stage_ko: str | None = None
    stage_en: str | None = None


class TwelveStagesResult(BaseModel):
    policy_version: str | None = None
    policy_signature: str | None = None
    by_pillar: Dict[str, TwelveStagesPillar] = Field(default_factory=dict)
    summary: Dict[str, int] = Field(default_factory=dict)
    dominant: List[str] = Field(default_factory=list)
    weakest: List[str] = Field(default_factory=list)


class RelationsResult(BaseModel):
    priority_hit: str | None = None
    transform_to: str | None = None
    boosts: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    extras: Dict[str, Any] = Field(default_factory=dict)


class BanheGroups(BaseModel):
    five_he: Dict[str, Any] = Field(default_factory=dict)
    zixing: Dict[str, Any] = Field(default_factory=dict)
    banhe: List[Any] = Field(default_factory=list)


class RelationsExtras(BaseModel):
    banhe_groups: BanheGroups | None = None


class RelationsWeightedResult(BaseModel):
    policy_version: str | None = None
    policy_signature: str | None = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class StrengthDetails(BaseModel):
    month_state: int | None = None
    branch_root: int | None = None
    stem_visible: int | None = None
    combo_clash: int | None = None
    season_adjust: int | None = None
    month_stem_effect_applied: bool | None = None
    wealth_location_bonus_total: float | None = None
    wealth_location_hits: List[Dict[str, Any]] = Field(default_factory=list)


class StrengthResult(BaseModel):
    score_raw: float | None = None
    score: float | None = None
    score_normalized: float | None = None
    grade_code: str | None = None
    bin: str | None = None
    phase: str | None = None
    details: StrengthDetails | None = None
    policy: Dict[str, Any] = Field(default_factory=dict)


class StructureCandidate(BaseModel):
    id: str | None = None
    score: float | None = None
    notes: str | None = None


class StructureResultModel(BaseModel):
    primary: str | None = None
    confidence: float | None = None
    candidates: List[StructureCandidate] = Field(default_factory=list)


class LuckPillar(BaseModel):
    pillar: str | None = None
    start_age: float | None = None
    end_age: float | None = None
    index: int | None = None
    label: str | None = None
    clues: List[Any] = Field(default_factory=list)


class LuckResult(BaseModel):
    policy_version: str | None = None
    policy_signature: str | None = None
    direction: str | None = None
    start_age: float | None = None
    method: str | None = None
    pillars: List[LuckPillar] = Field(default_factory=list)
    current_luck: Dict[str, Any] | None = None


class LuckDirectionResult(BaseModel):
    direction: str | None = None
    method: str | None = None
    sex_at_birth: str | None = None


class ShenshaResult(BaseModel):
    enabled: bool = False
    list: List[Any] = Field(default_factory=list)


class SchoolProfileResult(BaseModel):
    id: str = "unknown"
    notes: str | None = None


class RecommendationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = False
    action: str = "none"
    copy_text: str | None = Field(default=None, alias="copy")


class LuckV112Frame(BaseModel):
    kind: Literal["year", "month", "day"] | None = None
    pillar: str | None = None
    start_dt: str | None = None
    end_dt: str | None = None
    score: float | None = None
    drivers: List[Dict[str, Any]] = Field(default_factory=list)
    tags: Dict[str, Any] = Field(default_factory=dict)
    explain: Dict[str, Any] = Field(default_factory=dict)


class LuckV112Result(BaseModel):
    policy_version: str | None = None
    annual: List[LuckV112Frame] = Field(default_factory=list)
    monthly: List[LuckV112Frame] = Field(default_factory=list)
    daily: List[LuckV112Frame] = Field(default_factory=list)
    transits: Dict[str, Any] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    """Input payload for analysis service."""

    pillars: dict[str, PillarInput]
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)


class AnalysisResponse(BaseModel):
    """Canonical response returned by the analysis API."""

    status: str = "success"
    season: str | None = None
    ten_gods: TenGodsResult = Field(default_factory=TenGodsResult)
    twelve_stages: TwelveStagesResult | None = None
    relations: RelationsResult = Field(default_factory=RelationsResult)
    relations_weighted: RelationsWeightedResult | None = None
    relations_extras: RelationsExtras = Field(default_factory=RelationsExtras)
    strength: StrengthResult = Field(default_factory=StrengthResult)
    strength_details: StrengthDetails | None = None
    structure: StructureResultModel | None = None
    climate: Dict[str, Any] = Field(default_factory=dict)
    yongshin: Dict[str, Any] = Field(default_factory=dict)
    luck: LuckResult = Field(default_factory=LuckResult)
    luck_v1_1_2: LuckV112Result | None = None
    luck_direction: LuckDirectionResult | None = None
    shensha: ShenshaResult = Field(default_factory=ShenshaResult)
    void: Dict[str, Any] | None = None
    yuanjin: Dict[str, Any] | None = None
    stage3: Dict[str, Any] = Field(default_factory=dict)
    elements_distribution_raw: Dict[str, float] = Field(default_factory=dict)
    elements_distribution: Dict[str, float] = Field(default_factory=dict)
    elements_distribution_transformed: Dict[str, float] = Field(default_factory=dict)
    combination_trace: List[Any] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    engine_summaries: Dict[str, Any] = Field(default_factory=dict)
    school_profile: SchoolProfileResult = Field(default_factory=SchoolProfileResult)
    recommendation: RecommendationResult = Field(default_factory=RecommendationResult)
    llm_guard: Dict[str, Any] = Field(default_factory=dict)
    text_guard: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
    trace: Dict[str, Any] = Field(default_factory=dict)
    compat_view: Dict[str, Any] = Field(default_factory=dict)
