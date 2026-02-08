"""Pydantic models for API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
    """Response payload for asynchronous URL-based processing jobs."""

    job_id: str
    status: str  # "queued" | "processing" | "done" | "error"
    error: str | None = None
    result: ProcessResponse | None = None
