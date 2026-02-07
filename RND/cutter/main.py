#!/usr/bin/env python3
import argparse
from pathlib import Path

from pydub import AudioSegment


def parse_timestamp(timestamp: str) -> int:
    """Parse a timestamp like '1.21' or '01:21' into milliseconds."""
    value = timestamp.strip()
    if ":" in value:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("Timestamp must be MM:SS or M.SS")
        minutes_str, seconds_str = parts
    else:
        parts = value.split(".")
        if len(parts) == 1:
            minutes_str, seconds_str = "0", parts[0]
        elif len(parts) == 2:
            minutes_str, seconds_str = parts
        else:
            raise ValueError("Timestamp must be MM:SS or M.SS")

    if not minutes_str.isdigit() or not seconds_str.isdigit():
        raise ValueError("Minutes and seconds must be numeric")

    minutes = int(minutes_str)
    seconds = int(seconds_str)
    if seconds >= 60:
        raise ValueError("Seconds must be between 0 and 59")

    return (minutes * 60 + seconds) * 1000


def cut_audio(input_path: Path, output_path: Path, timestamp_ms: int) -> None:
    audio = AudioSegment.from_file(input_path)
    if timestamp_ms < 0 or timestamp_ms > len(audio):
        raise ValueError("Timestamp is outside audio duration")

    clipped = audio[:timestamp_ms]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clipped.export(output_path, format=output_path.suffix.lstrip("."))


def main() -> None:
    parser = argparse.ArgumentParser(description="Cut an audio file at a timestamp.")
    parser.add_argument("input", type=Path, help="Input audio file path")
    parser.add_argument("timestamp", type=str, help="Timestamp (M.SS or MM:SS)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output audio file path (defaults to input name + _cut)",
    )
    args = parser.parse_args()

    timestamp_ms = parse_timestamp(args.timestamp)
    if args.output is None:
        output_path = args.input.with_name(
            f"{args.input.stem}_cut{args.input.suffix}"
        )
    else:
        output_path = args.output

    cut_audio(args.input, output_path, timestamp_ms)


if __name__ == "__main__":
    main()
