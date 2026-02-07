# Demucs learnings

- Easiest robust flow is CLI wrapping (`python -m demucs.separate`) instead of using Demucs internals directly.
- `--two-stems vocals` is key for this use case; it avoids handling 4 stems manually.
- The output path is nested as `<out>/<model>/<track_name>/...`; wrappers should normalize this.
- Demucs quality is usually strong on vocals, but CPU runtime can be noticeably slower than lighter models.
