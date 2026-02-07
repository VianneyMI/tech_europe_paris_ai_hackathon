# Troubleshooting Guide

## Demucs

### Error: missing `TorchCodec` / `No module named torchcodec`

Why this happens:
- `demucs` depends on `torchaudio` transitively.
- On some torch/torchaudio versions, audio IO paths require `torchcodec` at runtime.
- `torchcodec` is not always pulled automatically by all resolver/platform combinations.

Fix:
```bash
cd /Users/vianneymixtur/.codex/worktrees/b9c1/tech_europe_paris_ai_hackathon/RND/separation/demucs
uv add torchcodec
uv sync
```

### Error: `Couldn't find appropriate backend to handle uri ...`

Why this happens:
- `torchaudio` backend for writing WAV is missing in your env.

Fix:
```bash
cd /Users/vianneymixtur/.codex/worktrees/b9c1/tech_europe_paris_ai_hackathon/RND/separation/demucs
uv add soundfile
uv sync
```
Also ensure `ffmpeg` is installed and on PATH.

### Slow first run

Why this happens:
- Demucs downloads model weights on first use.

Fix:
- Wait for first run to complete once; subsequent runs are faster.

## Spleeter

### Native install fails on Apple Silicon / dependency resolver loops

Why this happens:
- Older Spleeter dependency chain can backtrack to legacy `numba/librosa` combinations.

Fix options:
1. Use Docker fallback via the included script (`python main.py ...`) with Docker installed.
2. Use a dedicated older Python env known to work with that dependency set.

## Open-Unmix

### Error: `Open-Unmix CLI umx not found`

Fix:
- Install `openunmix` in the same environment used to run the script.
- Or run the script with that env's Python directly.

## Generic checks

- Verify `ffmpeg`:
```bash
ffmpeg -version
```
- Verify Python env is the one you expect:
```bash
which python
python -V
```
- Verify tool CLI visibility:
```bash
which demucs
which spleeter
which umx
```
