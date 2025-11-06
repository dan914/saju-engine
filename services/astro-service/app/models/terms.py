from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TermQuery(BaseModel):
    """Input payload for querying solar terms."""

    year: int = Field(..., ge=1600, le=2200)
    timezone: str = Field(..., min_length=3)


class TermEntry(BaseModel):
    """Single solar term entry from the precomputed table."""

    term: str
    lambda_deg: float = Field(..., ge=0.0, le=360.0)
    utc_time: datetime
    local_time: datetime
    delta_t_seconds: float
    source: str
    algo_version: str


class TermResponse(BaseModel):
    """Response payload for term queries."""

    year: int
    timezone: str
    terms: list[TermEntry]
    trace: dict[str, Any] | None = None
