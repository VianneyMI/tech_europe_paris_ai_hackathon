from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import main


class OpenUnmixTests(unittest.TestCase):
    def test_separate_success_creates_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_audio = tmp_path / "song.mp3"
            input_audio.write_bytes(b"audio")
            out_dir = tmp_path / "out"

            def fake_run(cmd, *args, **kwargs):
                if cmd and cmd[0] == "umx":
                    stem_dir = out_dir / "_openunmix_raw" / "song"
                    stem_dir.mkdir(parents=True, exist_ok=True)
                    for stem in ["vocals.wav", "drums.wav", "bass.wav", "other.wav"]:
                        (stem_dir / stem).write_bytes(b"x")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                if cmd and cmd[0] == "ffmpeg":
                    music_out = out_dir / "song" / "music.wav"
                    music_out.parent.mkdir(parents=True, exist_ok=True)
                    music_out.write_bytes(b"m")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

            with patch("main.shutil.which", return_value="umx"):
                with patch("main.subprocess.run", side_effect=fake_run):
                    vocals, music = main.separate(input_audio, out_dir)

            self.assertTrue(vocals.exists())
            self.assertTrue(music.exists())
            self.assertEqual(vocals.name, "vocals.wav")
            self.assertEqual(music.name, "music.wav")

    def test_ffmpeg_failure_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_audio = tmp_path / "song.mp3"
            input_audio.write_bytes(b"audio")
            out_dir = tmp_path / "out"

            def fake_run(cmd, *args, **kwargs):
                if cmd and cmd[0] == "umx":
                    stem_dir = out_dir / "_openunmix_raw" / "song"
                    stem_dir.mkdir(parents=True, exist_ok=True)
                    for stem in ["vocals.wav", "drums.wav", "bass.wav", "other.wav"]:
                        (stem_dir / stem).write_bytes(b"x")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                return SimpleNamespace(returncode=1, stdout="", stderr="ffmpeg failed")

            with patch("main.shutil.which", return_value="umx"):
                with patch("main.subprocess.run", side_effect=fake_run):
                    with self.assertRaises(RuntimeError):
                        main.separate(input_audio, out_dir)


if __name__ == "__main__":
    unittest.main()
