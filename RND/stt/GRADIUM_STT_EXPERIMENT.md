# Gradium STT Experiment (Vocal-Only Audio)

Date: 2026-02-07

## Script

`RND/stt/gradium_transcribe.py`

Single-file CLI that:
- accepts a local vocal audio path
- auto-loads `GRADIUM_API_KEY` from environment (or `.env` if available)
- optionally preprocesses input via `ffmpeg` to mono 16 kHz WAV
- calls Gradium STT and prints transcript text

## Reproducible Run

### 1) Create a vocal-only sample

```bash
say -r 140 -o /tmp/gradium_lyrics2.aiff "When the night is falling down, we sing together, loud and clear."
ffmpeg -hide_banner -loglevel error -y -i /tmp/gradium_lyrics2.aiff /tmp/gradium_lyrics2.wav
```

### 2) Run transcription

```bash
uv run --python 3.13 --with gradium RND/stt/gradium_transcribe.py /tmp/gradium_lyrics2.wav
```

Observed output:

```text
# settings: base_url=https://eu.api.gradium.ai/api/ model_name=default input_format=wav
# preprocessing: ffmpeg mono/16k WAV
# request_id: xlJ-O0HBUmk
When the night is falling down, we sing together loud and clear
```

## Key Settings Used

- Base URL: `https://eu.api.gradium.ai/api/`
- STT endpoint: SDK default (`speech/asr`)
- `model_name`: `default`
- `input_format`: `wav`
- Preprocessing: `ffmpeg -ac 1 -ar 16000`
- Runtime: Python `3.13` with `gradium` package via `uv run --with gradium`
