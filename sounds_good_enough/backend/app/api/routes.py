"""HTTP routes for processing and file serving."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, cast
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import Settings
from app.models import LyricsTimestamp, ProcessJobResponse, ProcessResponse
from app.services.downloader import DownloadError, download_audio
from app.services.separator import SeparationError, separate
from app.services.transcriber import TranscriptionError, transcribe

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp3", ".wav"}
ALLOWED_MIME_PREFIX = "audio/"


@dataclass
class StoredJob:
    """Metadata describing files produced for a job."""

    path: Path
    created_at: float


@dataclass
class BackgroundJob:
    """Tracks the state of an asynchronous URL processing job."""

    job_id: str
    status: str = "queued"  # queued | processing | done | error
    error: str | None = None
    result: ProcessResponse | None = None
    task: asyncio.Task[None] | None = field(default=None, repr=False)


class UrlPayload(BaseModel):
    """Request body for the URL processing endpoint."""

    url: str


router = APIRouter(prefix="/api", tags=["api"])


def _validate_upload(file: UploadFile, settings: Settings) -> None:
    """Validate file extension and MIME type for uploaded audio files."""

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use .mp3 or .wav.")

    content_type = file.content_type or ""
    if not content_type.startswith(ALLOWED_MIME_PREFIX):
        raise HTTPException(status_code=400, detail="Unsupported content type. Audio files only.")

    if file.size is not None and file.size > settings.upload_max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.upload_max_mb}MB.",
        )


def _cleanup_expired_jobs(request: Request) -> None:
    """Remove expired job directories from in-memory job store."""

    settings: Settings = request.app.state.settings
    jobs: dict[str, StoredJob] = request.app.state.jobs
    now = time.time()
    expired = [
        job_id
        for job_id, job in jobs.items()
        if (
            now - job.created_at > settings.job_ttl_seconds
            and job_id != getattr(request.app.state, "demo_job_id", None)
        )
    ]
    for job_id in expired:
        job = jobs.pop(job_id)
        if job.path.exists():
            shutil.rmtree(job.path, ignore_errors=True)


@router.post("/process", response_model=ProcessResponse)
async def process_audio(
    request: Request,
    file: Annotated[UploadFile, File(...)],
) -> ProcessResponse:
    """Upload, separate, transcribe, and return lyrics with output URLs."""

    settings: Settings = request.app.state.settings
    _validate_upload(file, settings)
    _cleanup_expired_jobs(request)

    data = await file.read()
    if len(data) > settings.upload_max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.upload_max_mb}MB.",
        )

    file_hash = hashlib.sha256(data).hexdigest()
    jobs: dict[str, StoredJob] = request.app.state.jobs
    cache: dict[str, tuple[str, ProcessResponse]] = request.app.state.cache
    cached = cache.get(file_hash)
    if cached is not None:
        cached_job_id, cached_response = cached
        cached_job = jobs.get(cached_job_id)
        if cached_job is not None:
            vocals_path = cached_job.path / "vocals.wav"
            instrumental_path = cached_job.path / "instrumental.wav"
            if vocals_path.exists() and instrumental_path.exists():
                cached_job.created_at = time.time()
                return cached_response
        cache.pop(file_hash, None)

    if not settings.gradium_api_key.strip():
        raise HTTPException(status_code=500, detail="GRADIUM_API_KEY is missing.")

    job_id = str(uuid4())
    job_dir = Path(tempfile.mkdtemp(prefix=f"sge-{job_id}-"))
    input_path = job_dir / (file.filename or "input.wav")
    input_path.write_bytes(data)

    try:
        separation_result = await separate(
            input_path=input_path,
            output_dir=job_dir,
            model=settings.demucs_model,
            device=settings.demucs_device,
        )
        transcription = await transcribe(
            audio_path=separation_result.vocals_path,
            api_key=settings.gradium_api_key,
        )
    except SeparationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except TranscriptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = ProcessResponse(
        job_id=job_id,
        lyrics=transcription.text,
        lyrics_with_timestamps=[
            LyricsTimestamp(text=seg.text, start_s=seg.start_s, stop_s=seg.stop_s)
            for seg in transcription.segments
        ],
        vocals_url=f"/api/files/{job_id}/vocals.wav",
        instrumental_url=f"/api/files/{job_id}/instrumental.wav",
    )
    request.app.state.jobs[job_id] = StoredJob(path=job_dir, created_at=time.time())
    cache[file_hash] = (job_id, response)
    return response


@router.get("/demo", response_model=ProcessResponse)
async def get_demo(request: Request) -> ProcessResponse:
    """Return pre-seeded demo processing results when available."""

    demo_response = cast(ProcessResponse | None, getattr(request.app.state, "demo_response", None))
    if demo_response is None:
        raise HTTPException(status_code=404, detail="Demo data not available.")
    return demo_response


@router.get("/files/{job_id}/{filename}")
async def get_file(job_id: str, filename: str, request: Request) -> FileResponse:
    """Serve generated vocals or instrumental WAV files for a job."""

    if filename not in {"vocals.wav", "instrumental.wav"}:
        raise HTTPException(status_code=404, detail="Requested file is not available.")

    jobs: dict[str, StoredJob] = request.app.state.jobs
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    file_path = job.path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(path=file_path, media_type="audio/wav", filename=filename)


# ---------------------------------------------------------------------------
# Background URL processing helpers
# ---------------------------------------------------------------------------


async def _process_url_background(
    job: BackgroundJob,
    url: str,
    settings: Settings,
    jobs: dict[str, StoredJob],
) -> None:
    """Download YouTube audio, separate stems, transcribe – all in background."""

    job_id = job.job_id
    job_dir = Path(tempfile.mkdtemp(prefix=f"sge-{job_id}-"))

    try:
        job.status = "processing"

        # 1. Download audio from YouTube
        dl_result = await download_audio(url, job_dir)
        input_path = dl_result.audio_path

        # 2. Separate vocals / instrumental
        separation_result = await separate(
            input_path=input_path,
            output_dir=job_dir,
            model=settings.demucs_model,
            device=settings.demucs_device,
        )

        # 3. Transcribe vocals
        transcription = await transcribe(
            audio_path=separation_result.vocals_path,
            api_key=settings.gradium_api_key,
        )

        response = ProcessResponse(
            job_id=job_id,
            lyrics=transcription.text,
            lyrics_with_timestamps=[
                LyricsTimestamp(text=seg.text, start_s=seg.start_s, stop_s=seg.stop_s)
                for seg in transcription.segments
            ],
            vocals_url=f"/api/files/{job_id}/vocals.wav",
            instrumental_url=f"/api/files/{job_id}/instrumental.wav",
        )

        jobs[job_id] = StoredJob(path=job_dir, created_at=time.time())
        job.result = response
        job.status = "done"

    except (DownloadError, SeparationError, TranscriptionError) as exc:
        job.status = "error"
        job.error = str(exc)
        logger.exception("Background URL processing failed for job %s", job_id)
    except Exception as exc:
        job.status = "error"
        job.error = f"Unexpected error: {exc}"
        logger.exception("Unexpected error in background URL processing for job %s", job_id)


# ---------------------------------------------------------------------------
# URL processing endpoints
# ---------------------------------------------------------------------------


@router.post("/process/url", response_model=ProcessJobResponse)
async def process_audio_from_url(
    request: Request,
    payload: UrlPayload,
) -> ProcessJobResponse:
    """Accept a YouTube URL and start background processing."""

    settings: Settings = request.app.state.settings

    if not settings.gradium_api_key.strip():
        raise HTTPException(status_code=500, detail="GRADIUM_API_KEY is missing.")

    _cleanup_expired_jobs(request)

    job_id = str(uuid4())
    bg_job = BackgroundJob(job_id=job_id)

    background_jobs: dict[str, BackgroundJob] = request.app.state.background_jobs
    stored_jobs: dict[str, StoredJob] = request.app.state.jobs

    bg_job.task = asyncio.create_task(
        _process_url_background(bg_job, payload.url, settings, stored_jobs),
    )
    background_jobs[job_id] = bg_job

    return ProcessJobResponse(job_id=job_id, status=bg_job.status)


@router.get("/jobs/{job_id}", response_model=ProcessJobResponse)
async def get_job_status(job_id: str, request: Request) -> ProcessJobResponse:
    """Return the current status of a background processing job."""

    background_jobs: dict[str, BackgroundJob] = request.app.state.background_jobs
    bg_job = background_jobs.get(job_id)

    if bg_job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    return ProcessJobResponse(
        job_id=bg_job.job_id,
        status=bg_job.status,
        error=bg_job.error,
        result=bg_job.result,
    )
