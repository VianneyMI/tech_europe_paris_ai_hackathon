from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _find_demucs_stem_dir(base_output: Path, model: str, input_file: Path) -> Path:
    # Demucs writes stems under: <out>/<model>/<track_name>/...
    # Some filenames can be slightly normalized by upstream code,
    # so we try exact path first, then a permissive glob fallback.
    expected = base_output / model / input_file.stem
    if expected.exists():
        return expected

    model_dir = base_output / model
    if not model_dir.exists():
        raise FileNotFoundError(f"Demucs model output directory not found: {model_dir}")

    candidates = [p for p in model_dir.glob(f"{input_file.stem}*") if p.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"No Demucs output directory found under: {model_dir}")
    return candidates[0]


def separate(input_audio: Path, output_dir: Path, model: str, device: str) -> tuple[Path, Path]:
    input_audio = input_audio.resolve()
    if not input_audio.exists() or not input_audio.is_file():
        raise FileNotFoundError(f"Input audio not found: {input_audio}")

    output_dir.mkdir(parents=True, exist_ok=True)
    # Keep raw tool output separate from normalized final outputs.
    demucs_tmp = output_dir / "_demucs_raw"
    demucs_tmp.mkdir(parents=True, exist_ok=True)

    # We intentionally call Demucs through its CLI module, not private Python APIs.
    # Why:
    # 1) CLI flags are stable and easy to reproduce from shell docs.
    # 2) This keeps our wrapper small and resilient to internal refactors.
    # 3) Using sys.executable ensures Demucs runs in the same Python env as this script.
    cmd = [
        sys.executable,
        "-m",
        "demucs.separate",
        "--two-stems",
        "vocals",
        "--device",
        device,
        "-n",
        model,
        "-o",
        str(demucs_tmp),
        str(input_audio),
    ]

    print(f"[demucs] Running: {' '.join(cmd)}")
    # capture_output=True lets us return concise, actionable error messages to users.
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Demucs separation failed: {detail}")

    stem_dir = _find_demucs_stem_dir(demucs_tmp, model, input_audio)

    vocals_src = stem_dir / "vocals.wav"
    music_src = stem_dir / "no_vocals.wav"
    if not vocals_src.exists() or not music_src.exists():
        raise FileNotFoundError(f"Expected Demucs stems missing in: {stem_dir}")

    track_out = output_dir / input_audio.stem
    track_out.mkdir(parents=True, exist_ok=True)

    # Normalize naming across all apps in this R&D:
    # Demucs emits `no_vocals.wav`; we expose `music.wav`.
    vocals_out = track_out / "vocals.wav"
    music_out = track_out / "music.wav"
    shutil.copy2(vocals_src, vocals_out)
    shutil.copy2(music_src, music_out)

    return vocals_out, music_out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split one audio file into vocals + music using Demucs.")
    parser.add_argument("input_audio", type=Path, help="Path to input audio file (wav/mp3).")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("./outputs"), help="Directory for outputs.")
    parser.add_argument("--model", "-m", default="htdemucs", help="Demucs model name.")
    parser.add_argument("--device", default="cpu", help="Device: cpu or cuda.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        vocals_out, music_out = separate(args.input_audio, args.output_dir, args.model, args.device)
    except Exception as exc:
        text = str(exc).lower()
        print(f"[demucs] ERROR: {exc}")
        if "torchcodec" in text:
            print("[demucs] Hint: install torchcodec in this env, then retry.")
            print(f"[demucs]   {sys.executable} -m pip install torchcodec")
        if "backend" in text or "couldn't find appropriate backend" in text:
            print("[demucs] Hint: install audio IO backends for torchaudio.")
            print(f"[demucs]   {sys.executable} -m pip install soundfile")
            print("[demucs]   and ensure ffmpeg is installed and on PATH")
        return 1

    print("[demucs] Separation complete")
    print(f"[demucs] vocals: {vocals_out}")
    print(f"[demucs] music:  {music_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
