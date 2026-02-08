"""HTTP routes for processing and file serving."""

from __future__ import annotations

import asyncio
import hashlib
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, cast
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.config import Settings
from app.models import LyricsTimestamp, ProcessJobResponse, ProcessResponse, ProcessUrlRequest
from app.services.separator import SeparationError, separate
from app.services.transcriber import TranscriptionError, transcribe
from app.services.video_source import DownloadedAudio, VideoDownloadError, normalize_youtube_source, resolve_youtube_audio

ALLOWED_EXTENSIONS = {".mp3", ".wav"}
ALLOWED_MIME_PREFIX = "audio/"
RUNNING_STATUSES = {"queued", "processing"}


@dataclass
class StoredJob:
    """Metadata describing files produced for a job."""

    path: Path
    created_at: float


@dataclass
class ProcessingJob:
    """Background processing status and optional payload."""

    status: str
    created_at: float
    source_key: str
    task: asyncio.Task[None] | None = None
    error: str | None = None
    result: ProcessResponse | None = None


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


def _get_cached_response(app_request: Request, file_hash: str) -> ProcessResponse | None:
    jobs: dict[str, StoredJob] = app_request.app.state.jobs
    cache: dict[str, tuple[str, ProcessResponse]] = app_request.app.state.cache
    cached = cache.get(file_hash)
    if cached is None:
        return None

    cached_job_id, cached_response = cached
    cached_job = jobs.get(cached_job_id)
    if cached_job is None:
        cache.pop(file_hash, None)
        return None

    vocals_path = cached_job.path / "vocals.wav"
    instrumental_path = cached_job.path / "instrumental.wav"
    if not vocals_path.exists() or not instrumental_path.exists():
        cache.pop(file_hash, None)
        return None

    cached_job.created_at = time.time()
    return cached_response


async def _create_job_response(
    request: Request,
    *,
    filename: str,
    input_bytes: bytes | None = None,
    input_source_path: Path | None = None,
) -> ProcessResponse:
    settings: Settings = request.app.state.settings
    if not settings.gradium_api_key.strip():
        raise HTTPException(status_code=500, detail="GRADIUM_API_KEY is missing.")

    job_id = str(uuid4())
    job_dir = Path(tempfile.mkdtemp(prefix=f"sge-{job_id}-"))
    input_path = job_dir / filename
    if input_bytes is not None:
        input_path.write_bytes(input_bytes)
    elif input_source_path is not None:
        await asyncio.to_thread(shutil.copy2, input_source_path, input_path)
    else:
        raise RuntimeError("Either input bytes or input source path is required.")

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
    return response


async def _process_with_hash(
    request: Request,
    *,
    file_hash: str,
    filename: str,
    input_bytes: bytes | None = None,
    input_source_path: Path | None = None,
) -> ProcessResponse:
    cached_response = _get_cached_response(request, file_hash)
    if cached_response is not None:
        return cached_response

    response = await _create_job_response(
        request,
        filename=filename,
        input_bytes=input_bytes,
        input_source_path=input_source_path,
    )
    request.app.state.cache[file_hash] = (response.job_id, response)
    return response


def _job_payload(job_id: str, job: ProcessingJob) -> ProcessJobResponse:
    return ProcessJobResponse(job_id=job_id, status=job.status, error=job.error, result=job.result)


async def _run_background_url_job(request: Request, job_id: str, source_url: str, source_key: str) -> None:
    jobs: dict[str, ProcessingJob] = request.app.state.processing_jobs
    job = jobs[job_id]
    job.status = "processing"

    settings: Settings = request.app.state.settings
    source_cache: dict[str, DownloadedAudio] = request.app.state.source_cache
    try:
        downloaded = await resolve_youtube_audio(
            source_url,
            cache_dir=Path(settings.youtube_cache_dir),
            known_sources=source_cache,
        )
        max_bytes = settings.upload_max_mb * 1024 * 1024
        if downloaded.path.stat().st_size > max_bytes:
            raise VideoDownloadError(f"Downloaded audio exceeds maximum size of {settings.upload_max_mb}MB.")

        result = await _process_with_hash(
            request,
            file_hash=downloaded.file_hash,
            filename="youtube_source.m4a",
            input_source_path=downloaded.path,
        )
        job.result = result
        job.status = "done"
    except (VideoDownloadError, SeparationError, TranscriptionError, HTTPException) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        job.error = detail or "Background processing failed."
        job.status = "error"
    except Exception as exc:  # pragma: no cover - safety net
        job.error = f"Unexpected background processing error: {exc}"
        job.status = "error"
    finally:
        source_to_job: dict[str, str] = request.app.state.source_to_job
        if source_to_job.get(source_key) != job_id:
            return
        if job.status == "error":
            source_to_job.pop(source_key, None)


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
    try:
        return await _process_with_hash(
            request,
            file_hash=file_hash,
            filename=file.filename or "input.wav",
            input_bytes=data,
        )
    except SeparationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except TranscriptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/process/url", response_model=ProcessJobResponse, status_code=202)
async def process_from_url(request: Request, payload: ProcessUrlRequest) -> ProcessJobResponse:
    """Queue a YouTube URL for background processing and return job metadata."""

    raw_url = payload.url.strip()
    if not raw_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://.")

    source_key = normalize_youtube_source(raw_url)
    source_to_job: dict[str, str] = request.app.state.source_to_job
    jobs: dict[str, ProcessingJob] = request.app.state.processing_jobs
    existing_job_id = source_to_job.get(source_key)
    if existing_job_id:
        existing_job = jobs.get(existing_job_id)
        if existing_job is not None and existing_job.status in RUNNING_STATUSES.union({"done"}):
            return _job_payload(existing_job_id, existing_job)

    job_id = str(uuid4())
    job = ProcessingJob(status="queued", created_at=time.time(), source_key=source_key)
    jobs[job_id] = job
    source_to_job[source_key] = job_id
    task = asyncio.create_task(_run_background_url_job(request, job_id, raw_url, source_key))
    job.task = task
    return _job_payload(job_id, job)


@router.get("/jobs/{job_id}", response_model=ProcessJobResponse)
async def get_job(job_id: str, request: Request) -> ProcessJobResponse:
    """Return background processing status and result when available."""

    jobs: dict[str, ProcessingJob] = request.app.state.processing_jobs
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Processing job not found.")
    return _job_payload(job_id, job)


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
