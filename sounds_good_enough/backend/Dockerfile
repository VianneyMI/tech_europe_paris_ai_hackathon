FROM python:3.13-slim

# System dependencies (ffmpeg for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Pre-download Demucs model (~300 MB) to avoid cold-start delay
RUN uv run python -c "from demucs.pretrained import get_model; get_model('htdemucs')"

# Copy application code
COPY app/ app/
COPY demo_data/ demo_data/

EXPOSE 8000

# Railway sets PORT env var; fall back to 8000 for local use
CMD uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
