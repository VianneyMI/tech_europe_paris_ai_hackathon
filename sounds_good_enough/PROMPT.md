# Prompt: Build the "Sounds Good Enough" App

You are building a web application called **Sounds Good Enough** — a music-to-lyrics pipeline that takes an uploaded song, separates the vocals from the instrumental, and transcribes the vocals into text.

## Context

This is for a weekend hackathon (Tech Europe Paris, Feb 2026). The R&D phase is complete. Three stem separation tools were evaluated (Demucs, Spleeter, Open-Unmix) and **Demucs** was chosen for quality. A **Gradium STT** experiment was validated. Now we need a clean, working application.

The app lives in `sounds_good_enough/` with `backend/` and `frontend/` subdirectories.

### What the R&D proved

1. **Demucs separation works** via CLI subprocess wrapping (`python -m demucs.separate --two-stems vocals -n htdemucs`). Do NOT import Demucs internals — use `subprocess.run` with `sys.executable`. Output is `vocals.wav` + `no_vocals.wav` in a nested directory structure `<out>/<model>/<track_name>/`.

2. **Gradium STT works** via the `gradium` Python package. The SDK exposes two modes:
   - **Buffered** (preferred for this app): `result = await client.stt(setup, audio_bytes)` where `setup = {"model_name": "default", "input_format": "wav"}` and `audio_bytes` is the raw bytes of a WAV file. Returns an `STTResult` with `.text` (full transcription) and `.text_with_timestamps` (list of `TextWithTimestamps` with `.text`, `.start_s`, `.stop_s`).
   - **Streaming**: `stream = await client.stt_stream(setup, audio_generator)` — more complex, not needed here.
   - The client is created with `gradium.client.GradiumClient(api_key=...)` or reads from `GRADIUM_API_KEY` env var.
   - **Important**: When using `input_format: "wav"`, pass the full WAV file bytes directly (including header). No PCM conversion needed. When using `input_format: "pcm"` with numpy arrays, `sample_rate` must be `24000` and dtype must be `int16` or `float32`.

3. **Runtime dependencies**: `ffmpeg` must be on PATH. Demucs needs `torchcodec` and `soundfile` alongside `demucs>=4.0.1`. Gradium needs `gradium>=0.5.7`.

4. **First-run latency**: Demucs downloads model weights on first use (~hundreds of MB). Subsequent runs are faster.

5. **Gradium SDK internals** (from source inspection):
   - `STTSetup` is a TypedDict with fields: `model_name` (str, default "default"), `input_format` (str, default "wav"), `json_config` (optional).
   - `STTResult` is a dataclass: `text: str`, `text_with_timestamps: list[TextWithTimestamps]`, `request_id: str | None`.
   - `TextWithTimestamps` is a dataclass: `text: str`, `start_s: float`, `stop_s: float`.
   - The buffered `stt()` internally chunks bytes (4096-byte chunks for bytes input) and streams them over WebSocket.
   - Supported languages: English (en), French (fr), German (de), Spanish (es), Portuguese (pt).

## Application Requirements

### Functional

1. **Upload**: User uploads an audio file (mp3 or wav) through a web UI.
2. **Separate**: Backend runs Demucs 2-stem separation → produces `vocals.wav` (lyrics) and `no_vocals.wav` (instrumental/music).
3. **Transcribe**: Backend sends the vocals WAV bytes to Gradium STT → returns the transcribed lyrics as text with timestamps.
4. **Results**: The UI displays:
   - The transcribed lyrics (text), ideally with word-level timestamps
   - Audio players for both the vocals track and the instrumental track (so the user can listen/download)
5. **No persistence**: No database. Use temporary files/directories that are cleaned up. Processing state lives only in memory for the duration of the request.

### Non-Functional

- **Clean architecture**: Separation of concerns. The API layer should not contain business logic. Services should be independently testable.
- **Fully typed**: All function signatures must have type annotations. Use `mypy --strict` compatibility as a target.
- **Tested**: Unit tests with mocked external dependencies (subprocess for Demucs, HTTP/WebSocket for Gradium). At least one integration-style test for the API endpoints using FastAPI's `TestClient`.
- **Documented**: Docstrings on all public functions. A clear README with setup, run, and test instructions.
- **Error handling**: Graceful error messages for: unsupported file formats, Demucs failures, Gradium API errors, missing ffmpeg, missing API key.

## Tech Stack

### Backend

- **Python 3.13+**
- **FastAPI** for the HTTP API
- **UV** for dependency management (`pyproject.toml` + `uv.lock`)
- **Demucs** (`htdemucs` model, 2-stem mode, CPU default) for vocal separation
- **Gradium** (`gradium` Python package, buffered `client.stt()` mode) for speech-to-text
- **python-dotenv** for env var loading
- **pytest** + **pytest-asyncio** for testing

### Frontend

- **React 19** with **TypeScript**
- **Vite** for bundling
- Simple, clean UI — not a design showcase, but professional and usable
- A single page with: upload zone, processing status indicator, results section (lyrics text + two audio players)

## Project Structure

```
sounds_good_enough/
├── backend/
│   ├── pyproject.toml
│   ├── .env.example              # GRADIUM_API_KEY=gd_...
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app factory, CORS, lifespan
│   │   ├── config.py             # Settings via pydantic-settings (env vars)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py         # POST /api/process, GET /api/files/{job_id}/{filename}
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── separator.py      # Demucs wrapping (subprocess)
│   │   │   └── transcriber.py    # Gradium STT (buffered mode)
│   │   └── models.py             # Pydantic response models
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py           # Shared fixtures
│       ├── test_separator.py
│       ├── test_transcriber.py
│       └── test_api.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── components/
│       │   ├── UploadZone.tsx
│       │   ├── ProcessingStatus.tsx
│       │   └── Results.tsx
│       └── api/
│           └── client.ts         # Typed fetch wrapper for backend API
├── README.md
└── PROMPT.md                     # This file
```

## API Design

### `POST /api/process`

Accepts an audio file, runs separation + transcription, returns results.

- **Input**: `multipart/form-data` with a single `file` field (audio file, `.mp3` or `.wav`)
- **Validation**: Check file extension and MIME type. Reject anything that isn't audio.
- **Processing**:
  1. Save uploaded file to a temp directory
  2. Run Demucs separation (offloaded to a thread to avoid blocking the event loop)
  3. Read the resulting `vocals.wav` bytes
  4. Send to Gradium STT (buffered mode, `input_format: "wav"`)
  5. Collect transcription result
- **Output** (JSON):
  ```json
  {
    "job_id": "uuid-string",
    "lyrics": "the full transcribed text",
    "lyrics_with_timestamps": [
      {"text": "word", "start_s": 0.0, "stop_s": 0.5}
    ],
    "vocals_url": "/api/files/uuid-string/vocals.wav",
    "instrumental_url": "/api/files/uuid-string/instrumental.wav"
  }
  ```
- **Errors**: Return appropriate HTTP status codes (400 for bad input, 500 for processing failures) with `{"detail": "human-readable message"}`.

### `GET /api/files/{job_id}/{filename}`

Serves separated audio files.

- Allowed filenames: `vocals.wav`, `instrumental.wav`
- Returns 404 if the job_id or file doesn't exist
- Sets correct `Content-Type: audio/wav` header

### Job Cleanup Strategy

- Use Python's `tempfile.mkdtemp()` for each job.
- Store a dict `{job_id: (path, created_at)}` in app state.
- Clean up jobs older than a configurable TTL (default: 30 minutes) on a periodic background task, or on app shutdown via FastAPI lifespan.

## Service Implementation Details

### `separator.py`

```python
@dataclass
class SeparationResult:
    """Result of a Demucs stem separation."""
    vocals_path: Path
    instrumental_path: Path

async def separate(
    input_path: Path,
    output_dir: Path,
    model: str = "htdemucs",
    device: str = "cpu",
) -> SeparationResult:
    """Run Demucs 2-stem separation on an audio file.

    Wraps the Demucs CLI via subprocess. Runs in a thread pool to avoid
    blocking the async event loop.

    Returns a SeparationResult with paths to vocals.wav and instrumental.wav.
    Raises SeparationError on failure.
    """
```

Key implementation notes:
- Run Demucs via `subprocess.run([sys.executable, "-m", "demucs.separate", "--two-stems", "vocals", "-n", model, "--device", device, "-o", str(raw_output_dir), str(input_path)])`.
- Wrap the subprocess call in `asyncio.to_thread()` to avoid blocking the event loop.
- Demucs outputs to `<out>/<model>/<track_stem>/vocals.wav` and `<out>/<model>/<track_stem>/no_vocals.wav`.
- Copy and rename `no_vocals.wav` → `instrumental.wav` for clarity.
- Define a custom `SeparationError(Exception)` for clean error propagation.

### `transcriber.py`

```python
@dataclass
class TranscriptionSegment:
    """A single transcribed text segment with timing."""
    text: str
    start_s: float
    stop_s: float

@dataclass
class TranscriptionResult:
    """Full transcription result."""
    text: str
    segments: list[TranscriptionSegment]

async def transcribe(audio_path: Path, api_key: str) -> TranscriptionResult:
    """Transcribe a vocal audio file using Gradium STT (buffered mode).

    Reads the WAV file and sends it to Gradium's buffered STT endpoint.
    Returns the full transcription with word-level timestamps.
    Raises TranscriptionError on failure.
    """
```

Key implementation notes:
- Read the WAV file as bytes: `audio_bytes = audio_path.read_bytes()`
- Create the Gradium client: `client = gradium.client.GradiumClient(api_key=api_key)`
- Call buffered STT: `result = await client.stt(setup={"model_name": "default", "input_format": "wav"}, audio=audio_bytes)`
- Extract `result.text` and `result.text_with_timestamps`
- Define a custom `TranscriptionError(Exception)` for clean error propagation.
- **Do NOT convert to PCM** — just pass the WAV bytes directly. The Gradium SDK handles chunking internally (4096-byte chunks).

## Implementation Priorities

1. **Backend services first** (`separator.py`, `transcriber.py`) with their unit tests
2. **Config and models** (`config.py`, `models.py`)
3. **API layer** (`routes.py`, `main.py`) with integration test
4. **Frontend** (upload → status → results)
5. **README** and `.env.example`
6. **Integration**: wire frontend to backend, test end-to-end manually

## Quality Checklist

- [ ] All functions have type annotations and docstrings
- [ ] `mypy` passes (or very close to `--strict`)
- [ ] `pytest` passes with mocked externals
- [ ] `.env.example` documents required environment variables
- [ ] README covers: prerequisites (ffmpeg, Python 3.13+, Node 20+), setup, run, test
- [ ] Error states are handled in both backend and frontend
- [ ] No hardcoded paths — everything is configurable or uses temp dirs
- [ ] CORS is configured for local development (frontend on Vite port 5173, backend on uvicorn port 8000)
- [ ] Audio file size is bounded (e.g., 50MB max upload)

## What NOT to Do

- Do NOT use a database or any persistence layer.
- Do NOT import Demucs Python internals — use subprocess CLI wrapping only.
- Do NOT block the FastAPI event loop with synchronous Demucs calls — offload to a thread via `asyncio.to_thread()`.
- Do NOT hardcode the Gradium API key — load from environment.
- Do NOT convert WAV to PCM before sending to Gradium — the buffered `stt()` accepts WAV bytes directly with `input_format: "wav"`.
- Do NOT over-engineer: no message queues, no caching layers, no auth. Keep it simple.
- Do NOT skip error handling to save time. Graceful errors are non-negotiable.
- Do NOT use Spleeter or Open-Unmix — use Demucs only.
