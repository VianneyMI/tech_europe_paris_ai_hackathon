from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import main


class DemucsTests(unittest.TestCase):
    def test_separate_success_creates_normalized_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_audio = tmp_path / "song.mp3"
            input_audio.write_bytes(b"audio")
            out_dir = tmp_path / "out"

            def fake_run(*args, **kwargs):
                stem_dir = out_dir / "_demucs_raw" / "htdemucs" / "song"
                stem_dir.mkdir(parents=True, exist_ok=True)
                (stem_dir / "vocals.wav").write_bytes(b"v")
                (stem_dir / "no_vocals.wav").write_bytes(b"m")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch("main.subprocess.run", side_effect=fake_run):
                vocals, music = main.separate(input_audio, out_dir, "htdemucs", "cpu")

            self.assertTrue(vocals.exists())
            self.assertTrue(music.exists())
            self.assertEqual(vocals.name, "vocals.wav")
            self.assertEqual(music.name, "music.wav")

    def test_separate_missing_input_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                main.separate(tmp_path / "missing.mp3", tmp_path / "out", "htdemucs", "cpu")


if __name__ == "__main__":
    unittest.main()
