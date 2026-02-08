"""FastAPI app factory and lifespan configuration."""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import StoredJob, router
from app.config import Settings, get_settings

if TYPE_CHECKING:
    from app.models import ProcessResponse


async def _cleanup_loop(app: FastAPI) -> None:
    """Periodically delete expired job directories."""

    while True:
        await asyncio.sleep(app.state.settings.cleanup_interval_seconds)
        now = time.time()
        jobs = cast(dict[str, StoredJob], app.state.jobs)
        expired = [
            job_id
            for job_id, job in jobs.items()
            if now - job.created_at > app.state.settings.job_ttl_seconds
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
    app.state.cache = cast(dict[str, tuple[str, "ProcessResponse"]], {})
    cleanup_task = asyncio.create_task(_cleanup_loop(app))

    try:
        yield
    finally:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        jobs = cast(dict[str, StoredJob], app.state.jobs)
        for job in jobs.values():
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
