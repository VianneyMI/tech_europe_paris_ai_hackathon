# Stem Separation Learnings

## What stem separation is

Stem separation estimates source tracks (like vocals vs accompaniment) from a mixed song using ML models trained on multitrack data. For your target use case, we map outputs to:
- `vocals`: lyric content
- `music`: instrumental backing

## How to choose a tool

- Choose **Demucs** when quality is most important and you can tolerate slower CPU runtime.
- Choose **Spleeter** when you want a simple 2-stem CLI and your TensorFlow environment is compatible.
- Choose **Open-Unmix** for a predictable PyTorch CLI baseline and easy scripting.

## Common pitfalls and fixes

- Missing `ffmpeg`: mp3 inputs fail to decode. Install `ffmpeg` and retry.
- First-run delay: models download on first separation; cache persists for next runs.
- CPU-only slowness: prefer shorter clips for quick iteration, then run full tracks.
- GPU confusion: `cuda` works only if your PyTorch/TensorFlow build matches installed CUDA.
- Output path surprises: most tools nest output by model + track name; wrappers should normalize final filenames.
- Clipping after mixing stems: use controlled mixing (`ffmpeg amix` in this Open-Unmix app) and validate levels.

## Obstacles hit in this R&D

- Dependency ecosystems differ a lot across tools (PyTorch vs TensorFlow), so isolated per-tool environments are cleaner than one shared env.
- Tool CLIs output different stem names (`no_vocals`, `accompaniment`, separate drums/bass/other), so each wrapper normalizes to exactly `vocals.wav` + `music.wav`.
- On this Apple Silicon host, native Spleeter installation repeatedly backtracked into legacy `numba` builds and failed; Docker fallback is implemented but may be slow due amd64 emulation.
- Some advanced ecosystems (UVR/MDX) are powerful but less standardized for tiny reproducible scripts; documented in matrix but not selected for the three mini-app deliverables.

## Tight feedback loop tips

- Keep one tiny audio test clip (10-20s) for rapid smoke tests.
- Use per-tool project folders and `uv sync` once; reruns are much faster.
- Start on CPU defaults, then switch to GPU only after baseline correctness is verified.
