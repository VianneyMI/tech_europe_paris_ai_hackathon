"""Pydantic models for API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProcessUrlRequest(BaseModel):
    """Request payload for processing audio from an external URL."""

    url: str = Field(min_length=1)


class LyricsTimestamp(BaseModel):
    """A single transcribed token or segment with timing information."""

    text: str
    start_s: float = Field(ge=0)
    stop_s: float = Field(ge=0)


class ProcessResponse(BaseModel):
    """Response payload returned by the process endpoint."""

    job_id: str
    lyrics: str
    lyrics_with_timestamps: list[LyricsTimestamp]
    vocals_url: str
    instrumental_url: str


class ProcessJobResponse(BaseModel):
    """Background processing job state and optional result payload."""

    job_id: str
    status: str
    error: str | None = None
    result: ProcessResponse | None = None
