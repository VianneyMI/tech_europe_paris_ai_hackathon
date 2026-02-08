"""FastAPI app factory and lifespan configuration."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import shutil
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import BackgroundJob, StoredJob, router
from app.config import Settings, get_settings

if TYPE_CHECKING:
    from app.models import ProcessResponse

DEMO_JOB_ID = "demo-song"
DEMO_DIR = Path(__file__).resolve().parents[1] / "demo_data"


def _load_demo_data(app: FastAPI) -> None:
    """Load optional pre-seeded demo response and register it in app state."""

    from app.models import ProcessResponse

    response_path = DEMO_DIR / "response.json"
    if not response_path.exists():
        return

    raw = json.loads(response_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return

    file_hash = raw.pop("file_hash", None)
    response = ProcessResponse.model_validate(raw)
    app.state.jobs[DEMO_JOB_ID] = StoredJob(path=DEMO_DIR, created_at=time.time())
    app.state.demo_response = response

    if isinstance(file_hash, str) and file_hash.strip():
        app.state.cache[file_hash.strip()] = (DEMO_JOB_ID, response)
        return

    for candidate in ("input.wav", "input.mp3", "source.wav", "source.mp3"):
        source_path = DEMO_DIR / candidate
        if source_path.exists():
            app.state.cache[hashlib.sha256(source_path.read_bytes()).hexdigest()] = (DEMO_JOB_ID, response)
            break


async def _cleanup_loop(app: FastAPI) -> None:
    """Periodically delete expired job directories."""

    while True:
        await asyncio.sleep(app.state.settings.cleanup_interval_seconds)
        now = time.time()
        jobs = cast(dict[str, StoredJob], app.state.jobs)
        expired = [
            job_id
            for job_id, job in jobs.items()
            if (
                now - job.created_at > app.state.settings.job_ttl_seconds
                and job_id != cast(str | None, app.state.demo_job_id)
            )
        ]
        for job_id in expired:
            job = jobs.pop(job_id)
            if job.path.exists():
                shutil.rmtree(job.path, ignore_errors=True)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize in-memory state and cleanup worker, then teardown resources."""

    if not hasattr(app.state, "settings"):
        app.state.settings = get_settings()
    app.state.jobs = cast(dict[str, StoredJob], {})
    app.state.background_jobs = cast(dict[str, BackgroundJob], {})
    app.state.cache = cast(dict[str, tuple[str, "ProcessResponse"]], {})
    app.state.demo_job_id = cast(str | None, None)
    app.state.demo_response = cast("ProcessResponse | None", None)
    app.state.demo_job_id = DEMO_JOB_ID
    _load_demo_data(app)
    cleanup_task = asyncio.create_task(_cleanup_loop(app))

    try:
        yield
    finally:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        jobs = cast(dict[str, StoredJob], app.state.jobs)
        demo_job_id = cast(str | None, app.state.demo_job_id)
        for job_id, job in jobs.items():
            if job_id == demo_job_id:
                continue
            if job.path.exists():
                shutil.rmtree(job.path, ignore_errors=True)


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI app instance."""

    app = FastAPI(title="Sounds Good Enough", lifespan=lifespan)
    effective_settings = app_settings or get_settings()
    app.state.settings = effective_settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=effective_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
