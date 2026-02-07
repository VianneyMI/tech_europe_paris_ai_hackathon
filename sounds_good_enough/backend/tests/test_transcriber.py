"""Unit tests for the Gradium transcription service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from app.services.transcriber import TranscriptionError, transcribe


@dataclass(frozen=True)
class _Segment:
    text: str
    start_s: float
    stop_s: float


@dataclass(frozen=True)
class _Result:
    text: str
    text_with_timestamps: list[_Segment]


class _FakeClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def stt(self, setup: dict[str, Any], audio: bytes) -> _Result:
        assert setup["input_format"] == "wav"
        assert audio.startswith(b"RIFF")
        return _Result(
            text="hello world",
            text_with_timestamps=[_Segment(text="hello", start_s=0.0, stop_s=0.4)],
        )


@pytest.mark.asyncio
async def test_transcribe_success(monkeypatch: pytest.MonkeyPatch, temp_audio_file: Path) -> None:
    """Transcriber maps Gradium response into domain model."""

    from app.services import transcriber as module

    monkeypatch.setattr(module, "GradiumClient", _FakeClient)

    result = await transcribe(audio_path=temp_audio_file, api_key="gd_test")

    assert result.text == "hello world"
    assert result.segments[0].text == "hello"


@pytest.mark.asyncio
async def test_transcribe_error(monkeypatch: pytest.MonkeyPatch, temp_audio_file: Path) -> None:
    """Transcriber wraps provider exceptions as TranscriptionError."""

    class _BadClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

        async def stt(self, setup: dict[str, Any], audio: bytes) -> _Result:
            raise RuntimeError("network failed")

    from app.services import transcriber as module

    monkeypatch.setattr(module, "GradiumClient", _BadClient)

    with pytest.raises(TranscriptionError, match="Gradium transcription failed"):
        await transcribe(audio_path=temp_audio_file, api_key="gd_test")
