import asyncio
import os
import sys
import gradium
from pathlib import Path
from dotenv import load_dotenv

def _ensure_supported_python() -> None:
    required = (3, 13)
    if sys.version_info < required:
        raise RuntimeError(
            "This script requires Python 3.13+. "
            f"Current interpreter: {sys.executable} "
            f"({sys.version.split()[0]}). "
            "Try running with `uv run python main.py` or "
            "ensure the local version in `.python-version` is active."
        )


_ensure_supported_python()
load_dotenv()


def load_audio_data(audio_path: str) -> bytes:
    with open(audio_path, "rb") as f:
        return f.read()

async def main(audio_data: bytes):
    client = gradium.client.GradiumClient(api_key=os.getenv("GRADIUM_API_KEY"))

    # Audio generator that yields audio chunks
    async def audio_generator(audio_data, chunk_size=1920):
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i : i + chunk_size]

    # Create STT stream
    stream = await client.stt_stream(
        {"model_name": "default", "input_format": "pcm"},
        audio_generator(audio_data),
    )

    # Process transcription results
    async for message in stream.iter_text():
        print(message)

if __name__ == "__main__":
    path_to_audio = Path(__file__).parent / "data" / "input" / "vocals.wav"
    asyncio.run(main(load_audio_data(path_to_audio)))