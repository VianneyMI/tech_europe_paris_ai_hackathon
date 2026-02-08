"""YouTube audio download service using yt-dlp."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path


class DownloadError(Exception):
    """Raised when downloading audio from a URL fails."""


@dataclass(frozen=True)
class DownloadResult:
    """Result of a successful audio download."""

    audio_path: Path


# Loose check – accepts youtube.com and youtu.be links.
_YOUTUBE_URL_RE = re.compile(
    r"^https?://(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/",
)


def _is_youtube_url(url: str) -> bool:
    return _YOUTUBE_URL_RE.match(url) is not None


def _download_audio(url: str, output_dir: Path) -> Path:
    """Download audio from *url* into *output_dir* and return the file path."""
    import yt_dlp  # type: ignore[import-untyped]

    output_template = str(output_dir / "%(id)s.%(ext)s")

    ydl_opts: dict[str, object] = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info: dict[str, object] = ydl.extract_info(url, download=True)  # type: ignore[assignment]

    video_id = info.get("id", "audio")
    # yt-dlp may produce a .wav via the postprocessor
    expected_wav = output_dir / f"{video_id}.wav"
    if expected_wav.exists():
        return expected_wav

    # Fallback: find any audio file produced in the directory
    for candidate in sorted(output_dir.iterdir()):
        if candidate.suffix.lower() in {".wav", ".mp3", ".m4a", ".webm", ".opus"}:
            return candidate

    raise DownloadError("yt-dlp completed but no audio file was found in the output directory.")


async def download_audio(url: str, output_dir: Path) -> DownloadResult:
    """Download audio from a YouTube URL into *output_dir*.

    Raises ``DownloadError`` on failure.
    """
    if not _is_youtube_url(url):
        raise DownloadError("Only YouTube URLs are supported.")

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio_path = await asyncio.to_thread(_download_audio, url, output_dir)
    except DownloadError:
        raise
    except Exception as exc:
        raise DownloadError(f"Failed to download audio: {exc}") from exc

    return DownloadResult(audio_path=audio_path)
