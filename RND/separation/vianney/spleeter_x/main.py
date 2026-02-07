from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol
import typer

app = typer.Typer(help="Separate vocals from accompaniment using Spleeter.")


class SpleeterNotInstalledError(RuntimeError):
    """Raised when Spleeter is not available in the current environment."""


class SeparatorProtocol(Protocol):
    """Minimal protocol we need from a Spleeter separator instance."""

    def separate_to_file(self, audio_descriptor: str, destination: str) -> None: ...


def load_separator(model: str) -> SeparatorProtocol:
    """Load a Spleeter separator for a given model preset.

    This function isolates Spleeter imports, so other frameworks can import
    and use the core logic without hard dependencies at import time.
    """
    try:
        from spleeter.separator import Separator
    except ImportError as exc:
        raise SpleeterNotInstalledError(
            'Spleeter is not installed. Run: uv pip install --no-deps "spleeter==2.3.2"'
        ) from exc
    return Separator(model)


def separate_audio(
    input_audio: Path,
    output_dir: Path,
    model: str = "spleeter:2stems",
    separator: Optional[SeparatorProtocol] = None,
) -> Path:
    """Separate vocals from accompaniment and return the output directory.

    Args:
        input_audio: Path to the input audio file (wav, mp3, etc.).
        output_dir: Directory where separated stems will be written.
        model: Spleeter model preset (ex: "spleeter:2stems", "spleeter:4stems").
        separator: Optional pre-instantiated separator (useful for tests).

    Returns:
        The resolved output directory containing the separated stems.
    """
    input_audio = input_audio.expanduser().resolve()
    if not input_audio.exists():
        raise FileNotFoundError(f"Input audio does not exist: {input_audio}")
    if not input_audio.is_file():
        raise ValueError(f"Input audio must be a file: {input_audio}")

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    active_separator = separator or load_separator(model)
    active_separator.separate_to_file(str(input_audio), str(output_dir))
    return output_dir


@app.command("separate")
def separate_command(
    input_audio: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the input audio file.",
    ),
    output_dir: Path = typer.Option(
        Path("output"),
        "--output-dir",
        "-o",
        file_okay=False,
        dir_okay=True,
        help="Directory where separated stems will be written.",
    ),
    model: str = typer.Option(
        "spleeter:2stems",
        "--model",
        "-m",
        help="Spleeter model preset (ex: spleeter:2stems, spleeter:4stems).",
    ),
) -> None:
    """CLI entrypoint that wraps the core separation function."""
    try:
        typer.echo(f"Separating {input_audio} using {model}...")
        output_dir = separate_audio(input_audio=input_audio, output_dir=output_dir, model=model)
    except SpleeterNotInstalledError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Done. Stems written to {output_dir}.")


def main() -> None:
    """CLI main."""
    app()


if __name__ == "__main__":
    main()
