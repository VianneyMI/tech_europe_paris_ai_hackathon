from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import main


class SpleeterTests(unittest.TestCase):
    def test_builds_local_cli_cmd_when_spleeter_exists(self) -> None:
        input_audio = Path("/tmp/song.mp3")
        out_dir = Path("/tmp/out")
        with patch("main.shutil.which", side_effect=lambda name: "/usr/local/bin/spleeter" if name == "spleeter" else None):
            cmd = main._build_spleeter_cmd(input_audio, out_dir)
        self.assertEqual(cmd[0], "/usr/local/bin/spleeter")
        self.assertIn("separate", cmd)

    def test_builds_docker_cmd_when_spleeter_missing(self) -> None:
        input_audio = Path("/tmp/song.mp3")
        out_dir = Path("/tmp/out")

        def fake_which(name: str) -> str | None:
            if name == "spleeter":
                return None
            if name == "docker":
                return "/usr/bin/docker"
            return None

        with patch("main.shutil.which", side_effect=fake_which):
            cmd = main._build_spleeter_cmd(input_audio, out_dir)

        self.assertEqual(cmd[0], "/usr/bin/docker")
        self.assertEqual(cmd[1], "run")

    def test_separate_success_creates_normalized_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_audio = tmp_path / "song.mp3"
            input_audio.write_bytes(b"audio")
            out_dir = tmp_path / "out"

            def fake_run(*args, **kwargs):
                stem_dir = (out_dir / "_spleeter_raw" / "song").resolve()
                stem_dir.mkdir(parents=True, exist_ok=True)
                (stem_dir / "vocals.wav").write_bytes(b"v")
                (stem_dir / "accompaniment.wav").write_bytes(b"m")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch("main.shutil.which", side_effect=lambda name: "/usr/local/bin/spleeter" if name == "spleeter" else None):
                with patch("main.subprocess.run", side_effect=fake_run):
                    vocals, music = main.separate(input_audio, out_dir)

            self.assertTrue(vocals.exists())
            self.assertTrue(music.exists())
            self.assertEqual(vocals.name, "vocals.wav")
            self.assertEqual(music.name, "music.wav")

    def test_subprocess_error_is_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_audio = tmp_path / "song.mp3"
            input_audio.write_bytes(b"audio")

            with patch("main.shutil.which", side_effect=lambda name: "/usr/local/bin/spleeter" if name == "spleeter" else None):
                with patch(
                    "main.subprocess.run",
                    return_value=SimpleNamespace(returncode=1, stdout="", stderr="boom"),
                ):
                    with self.assertRaises(RuntimeError):
                        main.separate(input_audio, tmp_path / "out")


if __name__ == "__main__":
    unittest.main()
