"""Integration-style API tests for processing and file serving."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes
from app.services.separator import SeparationResult
from app.services.transcriber import TranscriptionResult, TranscriptionSegment


def test_process_and_files_flow(monkeypatch, client: TestClient) -> None:
    """The process endpoint returns metadata and generated files are downloadable."""

    async def fake_separate(
        input_path: Path,
        output_dir: Path,
        model: str = "htdemucs",
        device: str = "cpu",
    ) -> SeparationResult:
        vocals = output_dir / "vocals.wav"
        instrumental = output_dir / "instrumental.wav"
        vocals.write_bytes(b"vocals-audio")
        instrumental.write_bytes(b"inst-audio")
        return SeparationResult(vocals_path=vocals, instrumental_path=instrumental)

    async def fake_transcribe(audio_path: Path, api_key: str) -> TranscriptionResult:
        return TranscriptionResult(
            text="sample lyrics",
            segments=[TranscriptionSegment(text="sample", start_s=0.0, stop_s=0.6)],
        )

    monkeypatch.setattr(routes, "separate", fake_separate)
    monkeypatch.setattr(routes, "transcribe", fake_transcribe)

    response = client.post(
        "/api/process",
        files={"file": ("song.wav", b"RIFF....WAVE", "audio/wav")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["lyrics"] == "sample lyrics"

    vocals_resp = client.get(payload["vocals_url"])
    assert vocals_resp.status_code == 200
    assert vocals_resp.content == b"vocals-audio"

    inst_resp = client.get(payload["instrumental_url"])
    assert inst_resp.status_code == 200
    assert inst_resp.content == b"inst-audio"


def test_process_rejects_bad_format(client: TestClient) -> None:
    """Unsupported file extensions return HTTP 400."""

    response = client.post(
        "/api/process",
        files={"file": ("song.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_get_file_rejects_unknown_filename(client: TestClient) -> None:
    """Only vocals.wav and instrumental.wav are exposed."""

    response = client.get("/api/files/nonexistent/other.wav")
    assert response.status_code == 404


def test_process_uses_cache_for_identical_upload(monkeypatch, client: TestClient) -> None:
    """Processing the same file twice should use the in-memory cache on the second request."""

    call_counts = {"separate": 0, "transcribe": 0}

    async def fake_separate(
        input_path: Path,
        output_dir: Path,
        model: str = "htdemucs",
        device: str = "cpu",
    ) -> SeparationResult:
        call_counts["separate"] += 1
        vocals = output_dir / "vocals.wav"
        instrumental = output_dir / "instrumental.wav"
        vocals.write_bytes(b"vocals-audio")
        instrumental.write_bytes(b"inst-audio")
        return SeparationResult(vocals_path=vocals, instrumental_path=instrumental)

    async def fake_transcribe(audio_path: Path, api_key: str) -> TranscriptionResult:
        call_counts["transcribe"] += 1
        return TranscriptionResult(
            text="cached lyrics",
            segments=[TranscriptionSegment(text="cached", start_s=0.0, stop_s=0.6)],
        )

    monkeypatch.setattr(routes, "separate", fake_separate)
    monkeypatch.setattr(routes, "transcribe", fake_transcribe)

    first_response = client.post(
        "/api/process",
        files={"file": ("repeat.wav", b"RIFF....WAVE", "audio/wav")},
    )
    second_response = client.post(
        "/api/process",
        files={"file": ("repeat.wav", b"RIFF....WAVE", "audio/wav")},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()
    assert call_counts["separate"] == 1
    assert call_counts["transcribe"] == 1
