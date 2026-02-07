"""Demucs-backed stem separation service."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class SeparationError(Exception):
    """Raised when Demucs separation fails."""


@dataclass(frozen=True)
class SeparationResult:
    """Result of Demucs stem separation."""

    vocals_path: Path
    instrumental_path: Path


def _run_demucs(input_path: Path, output_root: Path, model: str, device: str) -> None:
    """Run Demucs as a subprocess and raise SeparationError on failure."""

    command = [
        sys.executable,
        "-m",
        "demucs.separate",
        "--two-stems",
        "vocals",
        "-n",
        model,
        "--device",
        device,
        "-o",
        str(output_root),
        str(input_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise SeparationError("Demucs is not available in the current Python environment.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "No error details provided."
        if "ffmpeg" in stderr.lower():
            raise SeparationError("Demucs failed because ffmpeg is missing from PATH.") from exc
        raise SeparationError(f"Demucs separation failed: {stderr}") from exc


async def separate(
    input_path: Path,
    output_dir: Path,
    model: str = "htdemucs",
    device: str = "cpu",
) -> SeparationResult:
    """Run Demucs 2-stem separation and return vocals and instrumental paths."""

    raw_output_root = output_dir / "demucs_raw"
    raw_output_root.mkdir(parents=True, exist_ok=True)

    await asyncio.to_thread(_run_demucs, input_path, raw_output_root, model, device)

    track_stem = input_path.stem
    demucs_track_dir = raw_output_root / model / track_stem
    vocals_source = demucs_track_dir / "vocals.wav"
    instrumental_source = demucs_track_dir / "no_vocals.wav"

    if not vocals_source.exists() or not instrumental_source.exists():
        raise SeparationError(
            "Demucs completed but expected output files were not found."
        )

    vocals_target = output_dir / "vocals.wav"
    instrumental_target = output_dir / "instrumental.wav"

    shutil.copy2(vocals_source, vocals_target)
    shutil.copy2(instrumental_source, instrumental_target)

    return SeparationResult(vocals_path=vocals_target, instrumental_path=instrumental_target)
