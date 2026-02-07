# Spleeter (macOS arm64 install notes)

This folder sets up a working Spleeter environment on Apple Silicon where the
default `tensorflow` wheels do **not** exist. We install Spleeter without its
dependencies and then install the compatible `tensorflow-macos` variant.

## Prereqs

- Python `3.10.x` (Spleeter requires `<3.11`)
- Homebrew packages:

```sh
brew install ffmpeg libsndfile
```

## Install

From this folder:

```sh
uv venv
uv sync

# Install Spleeter itself without pulling its incompatible tensorflow wheel
uv pip install --no-deps "spleeter==2.3.2"
```

## Quick check

```sh
python -m spleeter separate -p spleeter:2stems -o output /path/to/song.mp3
```

You should get `vocals.wav` and `accompaniment.wav` in the output folder.

## Common issues

- **Python version error**: Spleeter requires `>=3.7.1,<3.11`. Ensure `.python-version`
  is `3.10` and recreate the venv.
- **TensorFlow wheel error on arm64**: This is expected for `tensorflow`. We avoid it
  by installing `tensorflow-macos` via `uv sync` and installing Spleeter with
  `--no-deps`.
- **Missing `ffmpeg` or `libsndfile`**: Install via Homebrew as shown above.