# Open-Unmix mini-app

## What it does
Runs Open-Unmix and exports:
- `vocals.wav`
- `music.wav` (sum of drums + bass + other via ffmpeg)

## Install
```bash
cd /Users/vianneymixtur/.codex/worktrees/b9c1/tech_europe_paris_ai_hackathon/RND/separation/openunmix
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
- Open-Unmix outputs 4 stems by default. This wrapper merges non-vocal stems for instrumental.
- CPU works; CUDA is automatic if PyTorch CUDA build is installed.
- Requires ffmpeg for mp3 and stem mixing step.
- The script auto-detects `umx` from PATH or from the current Python environment's `bin/` folder.
