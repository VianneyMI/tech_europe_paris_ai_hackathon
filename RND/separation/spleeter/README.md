# Spleeter mini-app

## What it does
Runs Spleeter in 2-stem mode and exports:
- `vocals.wav`
- `music.wav` (Spleeter `accompaniment.wav` renamed)

The script tries, in order:
1. Local `spleeter` CLI
2. `spleeter` executable next to current `python` binary
3. Docker fallback (`deezer/spleeter:3.8-2stems`)

## Install
```bash
cd /Users/vianneymixtur/.codex/worktrees/b9c1/tech_europe_paris_ai_hackathon/RND/separation/spleeter
uv sync
```

If native install is problematic on Apple Silicon, use Docker fallback by ensuring Docker Desktop is running.

## Run
```bash
python main.py /absolute/path/to/song.mp3 --output-dir ./outputs
```

## Test
```bash
python -m unittest -v
```

## Notes
- Native Spleeter install can be hard on Apple Silicon due old dependency constraints.
- Docker fallback is local and avoids Python dependency conflicts, but may be slower (amd64 emulation).
- Input decoding depends on ffmpeg in native mode.
