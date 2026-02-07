#!/usr/bin/env python3
"""Transcribe isolated vocal audio with Gradium STT.

Usage:
  uv run --python 3.13 --with gradium python RND/stt/gradium_transcribe.py /path/to/vocals.wav
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import gradium


def load_api_key_from_dotenv_if_needed() -> None:
    if os.environ.get("GRADIUM_API_KEY"):
        return

    for candidate in (Path.cwd() / ".env", Path(__file__).resolve().parents[2] / ".env"):
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "GRADIUM_API_KEY":
                os.environ["GRADIUM_API_KEY"] = value.strip().strip("'").strip('"')
                return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe local vocal audio using Gradium speech-to-text."
    )
    parser.add_argument("audio_path", type=Path, help="Path to local vocal audio file.")
    parser.add_argument(
        "--base-url",
        default="https://eu.api.gradium.ai/api/",
        help="Gradium API base URL.",
    )
    parser.add_argument(
        "--model-name",
        default="default",
        help="STT model name (default: default).",
    )
    parser.add_argument(
        "--json-config",
        default=None,
        help="Optional JSON string passed as setup.json_config.",
    )
    parser.add_argument(
        "--no-preprocess",
        action="store_true",
        help="Disable ffmpeg preprocessing; send the input file as-is.",
    )
    return parser.parse_args()


def maybe_preprocess_to_wav(path: Path, disabled: bool) -> tuple[Path, str]:
    if disabled:
        return path, "as-is"

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return path, "as-is (ffmpeg not found)"

    tmp_dir = tempfile.mkdtemp(prefix="gradium_stt_")
    out = Path(tmp_dir) / "preprocessed.wav"
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out, "ffmpeg mono/16k WAV"


async def transcribe(
    *,
    audio_path: Path,
    base_url: str,
    model_name: str,
    json_config: str | None,
    no_preprocess: bool,
) -> str:
    if not audio_path.exists() or not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    load_api_key_from_dotenv_if_needed()
    api_key = os.environ.get("GRADIUM_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GRADIUM_API_KEY in environment.")

    processed_path, preprocessing_label = maybe_preprocess_to_wav(audio_path, no_preprocess)
    setup: dict[str, object] = {"model_name": model_name, "input_format": "wav"}
    if json_config is not None:
        setup["json_config"] = json.loads(json_config)

    client = gradium.client.GradiumClient(base_url=base_url, api_key=api_key)
    audio_bytes = processed_path.read_bytes()
    result = await client.stt(setup=setup, audio=audio_bytes)

    print(f"# settings: base_url={base_url} model_name={model_name} input_format=wav")
    print(f"# preprocessing: {preprocessing_label}")
    print(f"# request_id: {result.request_id}")
    print(result.text.strip())
    return result.text


def main() -> int:
    args = parse_args()
    try:
        asyncio.run(
            transcribe(
                audio_path=args.audio_path.resolve(),
                base_url=args.base_url,
                model_name=args.model_name,
                json_config=args.json_config,
                no_preprocess=args.no_preprocess,
            )
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
