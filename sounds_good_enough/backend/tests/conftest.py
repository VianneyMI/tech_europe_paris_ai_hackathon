"""Shared pytest fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def temp_audio_file() -> Iterator[Path]:
    """Create a temporary WAV file for tests."""

    with tempfile.TemporaryDirectory(prefix="sge-test-") as temp_dir:
        audio_path = Path(temp_dir) / "vocals.wav"
        audio_path.write_bytes(b"RIFF....WAVEfmt ")
        yield audio_path


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Create a test client with deterministic runtime settings."""

    monkeypatch.setenv("GRADIUM_API_KEY", "gd_test_key")
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
