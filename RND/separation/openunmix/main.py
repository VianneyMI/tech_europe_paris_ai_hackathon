from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def separate(input_audio: Path, output_dir: Path) -> tuple[Path, Path]:
    input_audio = input_audio.resolve()
    if not input_audio.exists() or not input_audio.is_file():
        raise FileNotFoundError(f"Input audio not found: {input_audio}")

    output_dir.mkdir(parents=True, exist_ok=True)
    umx_tmp = output_dir / "_openunmix_raw"
    umx_tmp.mkdir(parents=True, exist_ok=True)

    umx_bin = shutil.which("umx")
    if not umx_bin:
        candidate = Path(sys.executable).with_name("umx")
        if candidate.exists():
            umx_bin = str(candidate)
    if not umx_bin:
        raise RuntimeError("Open-Unmix CLI `umx` not found. Install openunmix in this Python environment.")

    cmd = [umx_bin, str(input_audio), "--outdir", str(umx_tmp)]
    print(f"[openunmix] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Open-Unmix separation failed: {detail}")

    stem_dir = umx_tmp / input_audio.stem
    vocals_src = stem_dir / "vocals.wav"
    drums_src = stem_dir / "drums.wav"
    bass_src = stem_dir / "bass.wav"
    other_src = stem_dir / "other.wav"

    required = [vocals_src, drums_src, bass_src, other_src]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        missing_text = ", ".join(missing)
        raise FileNotFoundError(f"Expected Open-Unmix stems missing: {missing_text}")

    track_out = output_dir / input_audio.stem
    track_out.mkdir(parents=True, exist_ok=True)
    vocals_out = track_out / "vocals.wav"
    music_out = track_out / "music.wav"

    shutil.copy2(vocals_src, vocals_out)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(drums_src),
        "-i",
        str(bass_src),
        "-i",
        str(other_src),
        "-filter_complex",
        "amix=inputs=3:normalize=0",
        str(music_out),
    ]
    mix_result = subprocess.run(ffmpeg_cmd, text=True, capture_output=True)
    if mix_result.returncode != 0:
        detail = (mix_result.stderr or mix_result.stdout or "").strip()
        raise RuntimeError(f"ffmpeg mix failed: {detail}")

    return vocals_out, music_out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split one audio file into vocals + music using Open-Unmix.")
    parser.add_argument("input_audio", type=Path, help="Path to input audio file (wav/mp3).")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("./outputs"), help="Directory for outputs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        vocals_out, music_out = separate(args.input_audio, args.output_dir)
    except Exception as exc:
        print(f"[openunmix] ERROR: {exc}")
        return 1

    print("[openunmix] Separation complete")
    print(f"[openunmix] vocals: {vocals_out}")
    print(f"[openunmix] music:  {music_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
