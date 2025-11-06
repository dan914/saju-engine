from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TimeEvent(BaseModel):
    """Describes a timezone transition or notable event."""

    iana: str
    kind: str = Field(..., description="transition|dst|policy")
    effective_from: datetime | None = None
    notes: str | None = None


class TimeConversionRequest(BaseModel):
    """Request payload for UTC/local conversions."""

    instant: datetime
    source_tz: str
    target_tz: str


class TimeConversionResponse(BaseModel):
    """Response payload containing converted instants and trace metadata."""

    input: TimeConversionRequest
    converted: datetime
    tzdb_version: str
    events: list[TimeEvent]
    trace: dict[str, Any] | None = None
