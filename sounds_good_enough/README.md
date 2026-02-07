# Sounds Good Enough

A weekend-hackathon app that:
1. Accepts an uploaded MP3/WAV file.
2. Separates vocals and instrumental stems with Demucs.
3. Sends `vocals.wav` to Gradium STT (buffered mode).
4. Returns lyrics + timestamps and serves both separated WAV files.

## Stack

- Backend: Python 3.13+, FastAPI, Demucs, Gradium, UV
- Frontend: React 19, TypeScript, Vite

## Prerequisites

- Python 3.13+
- Node.js 20+
- `ffmpeg` on your `PATH`
- Gradium API key

## Backend Setup

```bash
cd sounds_good_enough/backend
cp .env.example .env
# Edit .env and set GRADIUM_API_KEY
uv sync --group dev
```

Run backend:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:

- `POST /api/process` (multipart: `file`)
- `GET /api/files/{job_id}/{filename}` (`vocals.wav` or `instrumental.wav`)

## Frontend Setup

```bash
cd sounds_good_enough/frontend
npm install
npm run dev
```

Frontend defaults to backend at `http://localhost:8000`.
Override with:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Tests and Type Checks

Backend tests:

```bash
cd sounds_good_enough/backend
uv run pytest
```

Backend strict typing:

```bash
cd sounds_good_enough/backend
uv run mypy app
```

Frontend build check:

```bash
cd sounds_good_enough/frontend
npm run build
```

## Notes

- First Demucs run can be slow due to model weight download.
- No database is used; job files are stored in temp directories and cleaned up by TTL and app shutdown.
- Upload limit defaults to 50MB.

## Config

Backend settings are read from environment variables (`app/config.py`):

- `GRADIUM_API_KEY` (required for transcription)
- `demucs_model` (default: `htdemucs`)
- `demucs_device` (default: `cpu`)
- `upload_max_mb` (default: `50`)
- `job_ttl_seconds` (default: `1800`)
- `cleanup_interval_seconds` (default: `300`)
