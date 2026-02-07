"""Gradium-backed transcription service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gradium.client import GradiumClient


class TranscriptionError(Exception):
    """Raised when transcription fails."""


@dataclass(frozen=True)
class TranscriptionSegment:
    """A single transcribed text segment with timing."""

    text: str
    start_s: float
    stop_s: float


@dataclass(frozen=True)
class TranscriptionResult:
    """Structured transcription result."""

    text: str
    segments: list[TranscriptionSegment]


async def transcribe(audio_path: Path, api_key: str) -> TranscriptionResult:
    """Transcribe a WAV vocals file using Gradium buffered STT mode."""

    if not api_key.strip():
        raise TranscriptionError("Gradium API key is missing.")

    try:
        audio_bytes = audio_path.read_bytes()
    except OSError as exc:
        raise TranscriptionError("Failed to read vocals audio for transcription.") from exc

    client = GradiumClient(api_key=api_key)
    setup: dict[str, Any] = {"model_name": "default", "input_format": "wav"}

    try:
        result = await client.stt(setup=setup, audio=audio_bytes)
    except Exception as exc:  # pragma: no cover - wrapped for clear domain error
        raise TranscriptionError(f"Gradium transcription failed: {exc}") from exc

    segments = [
        TranscriptionSegment(text=item.text, start_s=item.start_s, stop_s=item.stop_s)
        for item in result.text_with_timestamps
    ]
    return TranscriptionResult(text=result.text, segments=segments)
