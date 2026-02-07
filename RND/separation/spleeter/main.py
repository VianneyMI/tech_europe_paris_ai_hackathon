from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _build_spleeter_cmd(input_audio: Path, out_dir: Path) -> list[str]:
    local_spleeter = shutil.which("spleeter")
    if not local_spleeter:
        candidate = Path(sys.executable).with_name("spleeter")
        if candidate.exists():
            local_spleeter = str(candidate)
    if local_spleeter:
        return [
            local_spleeter,
            "separate",
            "-p",
            "spleeter:2stems",
            "-o",
            str(out_dir),
            str(input_audio),
        ]

    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError(
            "Neither `spleeter` nor `docker` was found on PATH. Install one of them."
        )

    return [
        docker,
        "run",
        "--rm",
        "-v",
        f"{input_audio.parent}:/input",
        "-v",
        f"{out_dir}:/output",
        "deezer/spleeter:3.8-2stems",
        "separate",
        "-p",
        "spleeter:2stems",
        "-o",
        "/output",
        f"/input/{input_audio.name}",
    ]


def separate(input_audio: Path, output_dir: Path) -> tuple[Path, Path]:
    input_audio = input_audio.resolve()
    if not input_audio.exists() or not input_audio.is_file():
        raise FileNotFoundError(f"Input audio not found: {input_audio}")

    output_dir.mkdir(parents=True, exist_ok=True)
    spleeter_tmp = (output_dir / "_spleeter_raw").resolve()
    spleeter_tmp.mkdir(parents=True, exist_ok=True)

    cmd = _build_spleeter_cmd(input_audio, spleeter_tmp)

    print(f"[spleeter] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Spleeter separation failed: {detail}")

    stem_dir = spleeter_tmp / input_audio.stem
    vocals_src = stem_dir / "vocals.wav"
    music_src = stem_dir / "accompaniment.wav"
    if not vocals_src.exists() or not music_src.exists():
        raise FileNotFoundError(f"Expected Spleeter stems missing in: {stem_dir}")

    track_out = output_dir / input_audio.stem
    track_out.mkdir(parents=True, exist_ok=True)

    vocals_out = track_out / "vocals.wav"
    music_out = track_out / "music.wav"
    shutil.copy2(vocals_src, vocals_out)
    shutil.copy2(music_src, music_out)

    return vocals_out, music_out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split one audio file into vocals + music using Spleeter.")
    parser.add_argument("input_audio", type=Path, help="Path to input audio file (wav/mp3).")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("./outputs"), help="Directory for outputs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        vocals_out, music_out = separate(args.input_audio, args.output_dir)
    except Exception as exc:
        print(f"[spleeter] ERROR: {exc}")
        return 1

    print("[spleeter] Separation complete")
    print(f"[spleeter] vocals: {vocals_out}")
    print(f"[spleeter] music:  {music_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
