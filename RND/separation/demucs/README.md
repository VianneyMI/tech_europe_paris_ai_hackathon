# Demucs mini-app

## What it does
Runs Demucs in 2-stem mode and exports:
- `vocals.wav`
- `music.wav` (Demucs `no_vocals.wav` renamed)

## How Demucs works (short version)

- Demucs is a source separation model that takes a mixed track and predicts source stems.
- In this app we run it with `--two-stems vocals`, so Demucs outputs:
  - `vocals.wav`
  - `no_vocals.wav`
- We then rename `no_vocals.wav` to `music.wav` so every app in this R&D exposes the same output contract.

## How Demucs is usually used

Demucs is commonly invoked from CLI:

```bash
python -m demucs.separate --two-stems vocals -n htdemucs -o ./out /path/to/song.mp3
```

Typical output layout:

```text
out/
  htdemucs/
    song/
      vocals.wav
      no_vocals.wav
```

## Why this app uses `subprocess`

This wrapper calls Demucs CLI via `subprocess.run(...)` instead of importing Demucs internals directly.

Reasons:
- CLI flags are stable and easier to reason about than internal APIs.
- It keeps this script small and robust against Demucs internal refactors.
- It mirrors exactly what you would run manually in shell, which makes debugging easier.
- Using `sys.executable -m demucs.separate` guarantees we use the same Python environment as this script.

Interface choice in this app:
- Input: one local file path (`wav`/`mp3`)
- Engine: Demucs CLI in 2-stem vocal mode
- Output normalization:
  - copy `vocals.wav` -> `vocals.wav`
  - copy `no_vocals.wav` -> `music.wav`
- Final location:
  - `<output-dir>/<track-name>/vocals.wav`
  - `<output-dir>/<track-name>/music.wav`

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
- This app declares `torchcodec` and `soundfile` explicitly because some Demucs/torchaudio combos require them at runtime.

## Troubleshooting
- See `/Users/vianneymixtur/.codex/worktrees/b9c1/tech_europe_paris_ai_hackathon/RND/separation/TROUBLESHOOTING.md`
- Common Demucs issue: missing `torchcodec` or missing torchaudio backend for WAV writes.
