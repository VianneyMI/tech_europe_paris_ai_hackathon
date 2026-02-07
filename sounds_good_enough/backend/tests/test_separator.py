"""Unit tests for the Demucs separator service."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from app.services.separator import SeparationError, separate


@pytest.mark.asyncio
async def test_separate_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The separator returns copied vocals and instrumental files."""

    input_path = tmp_path / "song.wav"
    input_path.write_bytes(b"audio")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        command = args[0]
        output_dir = Path(command[10])
        model = command[6]
        track_dir = output_dir / model / "song"
        track_dir.mkdir(parents=True, exist_ok=True)
        (track_dir / "vocals.wav").write_bytes(b"vocals")
        (track_dir / "no_vocals.wav").write_bytes(b"inst")
        return subprocess.CompletedProcess(args=[], returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = await separate(input_path=input_path, output_dir=tmp_path / "out")

    assert result.vocals_path.read_bytes() == b"vocals"
    assert result.instrumental_path.read_bytes() == b"inst"


@pytest.mark.asyncio
async def test_separate_demucs_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A Demucs subprocess failure is wrapped in SeparationError."""

    input_path = tmp_path / "song.wav"
    input_path.write_bytes(b"audio")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["python", "-m", "demucs.separate"],
            stderr="something bad happened",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(SeparationError, match="Demucs separation failed"):
        await separate(input_path=input_path, output_dir=tmp_path / "out")
