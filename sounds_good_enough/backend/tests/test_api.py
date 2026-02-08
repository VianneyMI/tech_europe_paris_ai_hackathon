"""Integration-style API tests for processing and file serving."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes
from app.services.separator import SeparationResult
from app.services.transcriber import TranscriptionResult, TranscriptionSegment
from app.services.video_source import DownloadedAudio


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


def test_demo_returns_404_without_seed_data(client: TestClient) -> None:
    """Demo endpoint should return 404 when demo data is not pre-seeded."""

    response = client.get("/api/demo")
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


def test_process_url_background_job(monkeypatch, client: TestClient, tmp_path: Path) -> None:
    """URL processing should run in background and expose result via job polling."""

    source_path = tmp_path / "source.m4a"
    source_path.write_bytes(b"yt-audio")

    async def fake_resolve_youtube_audio(
        url: str,
        cache_dir: Path,
        known_sources: dict[str, DownloadedAudio],
    ) -> DownloadedAudio:
        return DownloadedAudio(source_key="youtube:test123", path=source_path, file_hash="hash-123")

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
            text="youtube lyrics",
            segments=[TranscriptionSegment(text="youtube", start_s=0.0, stop_s=0.6)],
        )

    monkeypatch.setattr(routes, "resolve_youtube_audio", fake_resolve_youtube_audio)
    monkeypatch.setattr(routes, "separate", fake_separate)
    monkeypatch.setattr(routes, "transcribe", fake_transcribe)

    start = client.post("/api/process/url", json={"url": "https://www.youtube.com/watch?v=test123"})
    assert start.status_code == 202
    job_id = start.json()["job_id"]

    payload: dict[str, object] = {}
    for _ in range(50):
        poll = client.get(f"/api/jobs/{job_id}")
        assert poll.status_code == 200
        payload = poll.json()
        if payload["status"] == "done":
            break
        if payload["status"] == "error":
            raise AssertionError(f"Job unexpectedly failed: {payload['error']}")
        time.sleep(0.02)
    else:
        raise AssertionError("Background job did not complete in time.")

    assert payload["status"] == "done"
    result = payload["result"]
    assert isinstance(result, dict)
    assert result["lyrics"] == "youtube lyrics"


def test_process_url_reuses_existing_done_job(monkeypatch, client: TestClient, tmp_path: Path) -> None:
    """Submitting the same URL after success should return cached done job immediately."""

    source_path = tmp_path / "source.m4a"
    source_path.write_bytes(b"yt-audio")
    call_count = {"resolve": 0}

    async def fake_resolve_youtube_audio(
        url: str,
        cache_dir: Path,
        known_sources: dict[str, DownloadedAudio],
    ) -> DownloadedAudio:
        call_count["resolve"] += 1
        return DownloadedAudio(source_key="youtube:test123", path=source_path, file_hash="hash-123")

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
            text="youtube lyrics",
            segments=[TranscriptionSegment(text="youtube", start_s=0.0, stop_s=0.6)],
        )

    monkeypatch.setattr(routes, "resolve_youtube_audio", fake_resolve_youtube_audio)
    monkeypatch.setattr(routes, "separate", fake_separate)
    monkeypatch.setattr(routes, "transcribe", fake_transcribe)

    first = client.post("/api/process/url", json={"url": "https://youtu.be/test123"})
    assert first.status_code == 202
    first_job_id = first.json()["job_id"]
    for _ in range(50):
        poll = client.get(f"/api/jobs/{first_job_id}")
        assert poll.status_code == 200
        if poll.json()["status"] == "done":
            break
        time.sleep(0.02)

    second = client.post("/api/process/url", json={"url": "https://www.youtube.com/watch?v=test123"})
    assert second.status_code == 202
    second_payload = second.json()
    assert second_payload["status"] == "done"
    assert second_payload["job_id"] == first_job_id
    assert call_count["resolve"] == 1
