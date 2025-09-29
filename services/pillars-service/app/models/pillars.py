"""Data models for KR_classic v1.4 four pillars computation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PillarsComputeRequest(BaseModel):
    """Input payload for four pillars computation."""

    localDateTime: datetime = Field(..., alias="localDateTime")
    timezone: str
    rules: str = Field("KR_classic_v1.4", pattern="^KR_classic_v1\.4$")


class PillarComponent(BaseModel):
    """Single pillar element (e.g., year, month, day, hour)."""

    pillar: str
    boundaryUTC: datetime | None = None
    dayStartLocal: datetime | None = None
    rangeLocal: tuple[str, str] | None = None
    term: str | None = None
    lambda_deg: float | None = None
    policy: str | None = None
    rule: str | None = None


class PillarResult(BaseModel):
    """Container for the four pillars."""

    year: PillarComponent
    month: PillarComponent
    day: PillarComponent
    hour: PillarComponent


class TraceInfo(BaseModel):
    """Trace metadata describing calculation assumptions."""

    rule_id: str = Field("KR_classic_v1.4", alias="rule_id")
    deltaTSeconds: float = Field(..., alias="deltaTSeconds")
    tz: dict[str, str]
    astro: dict[str, float]
    boundaryPolicy: str
    epsilonSeconds: float
    flags: dict[str, bool]
    evidence: dict[str, object] | None = None


class PillarsComputeResponse(BaseModel):
    """API response wrapper for pillars computation."""

    pillars: PillarResult
    trace: TraceInfo

    class Config:
        allow_population_by_field_name = True
