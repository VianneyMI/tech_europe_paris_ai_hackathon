# Demucs mini-app

## What it does
Runs Demucs in 2-stem mode and exports:
- `vocals.wav`
- `music.wav` (Demucs `no_vocals.wav` renamed)

## Install
```bash
cd /Users/vianneymixtur/.codex/worktrees/b9c1/tech_europe_paris_ai_hackathon/RND/separation/demucs
uv sync
```

## Run
```bash
python main.py /absolute/path/to/song.mp3 --output-dir ./outputs
```

## Test
```bash
python -m unittest -v
```

## Notes
- First run downloads model weights.
- CPU is default (`--device cpu`).
- If you have GPU configured with PyTorch, use `--device cuda`.
