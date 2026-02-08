"""Utilities for downloading and caching audio from YouTube URLs."""

from __future__ import annotations

import asyncio
import hashlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class VideoDownloadError(Exception):
    """Raised when downloading an external video/audio source fails."""


@dataclass(frozen=True)
class DownloadedAudio:
    """Local audio artifact resolved from a source URL."""

    source_key: str
    path: Path
    file_hash: str


def normalize_youtube_source(url: str) -> str:
    """Return a stable cache key for known YouTube URL shapes."""

    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    video_id = ""

    if host in {"youtu.be", "www.youtu.be"}:
        video_id = path.split("/", maxsplit=1)[0]
    elif host.endswith("youtube.com"):
        if path == "watch":
            query = parse_qs(parsed.query)
            video_id = (query.get("v") or [""])[0]
        elif path.startswith("shorts/") or path.startswith("embed/"):
            video_id = path.split("/", maxsplit=1)[1]

    if video_id:
        return f"youtube:{video_id}"
    return f"url:{url.strip()}"


def _download_with_ytdlp(url: str, target_path: Path) -> None:
    """Download the best available audio stream into target_path."""

    target_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "-f",
        "bestaudio/best",
        "-o",
        str(target_path),
        url,
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "No error details provided."
        raise VideoDownloadError(f"Failed to download YouTube audio: {stderr}") from exc
    except FileNotFoundError as exc:
        raise VideoDownloadError("yt-dlp is not available in the current Python environment.") from exc


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def resolve_youtube_audio(
    url: str,
    cache_dir: Path,
    known_sources: dict[str, DownloadedAudio],
) -> DownloadedAudio:
    """Resolve URL into a cached local audio file, downloading only when needed."""

    source_key = normalize_youtube_source(url)
    cached = known_sources.get(source_key)
    if cached is not None and cached.path.exists():
        return cached

    target_path = cache_dir / f"{source_key.replace(':', '_')}.m4a"
    await asyncio.to_thread(_download_with_ytdlp, url, target_path)
    downloaded = DownloadedAudio(
        source_key=source_key,
        path=target_path,
        file_hash=await asyncio.to_thread(_hash_file, target_path),
    )
    known_sources[source_key] = downloaded
    return downloaded
