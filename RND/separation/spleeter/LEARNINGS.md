# Spleeter learnings

- Spleeter CLI is very simple for 2-stem use (`spleeter:2stems`).
- Main friction is dependency compatibility (TensorFlow + legacy librosa/numba constraints), especially on Apple Silicon.
- A practical workaround is Docker (`deezer/spleeter:3.8-2stems`), used as fallback when local CLI is missing.
- On ARM hosts, the available Spleeter Docker image may run under amd64 emulation and can be slow.
- Output naming is deterministic (`vocals.wav`, `accompaniment.wav`), so wrapping is straightforward.
