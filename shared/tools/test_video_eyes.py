# SPDX-License-Identifier: Apache-2.0
"""Tests for video_eyes.py (run: python -m unittest shared/tools/test_video_eyes.py). Uses a synthetic clip; skipped without ffmpeg."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ensure  # noqa: E402
import video_eyes  # noqa: E402

FF = ensure.ensure_ffmpeg()


@unittest.skipUnless(FF["ok"], "ffmpeg not installed")
class VideoEyes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.clip = Path(cls.td.name) / "clip.mp4"
        subprocess.run([FF["path"], "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=320x180:d=2",
                        "-f", "lavfi", "-i", "testsrc=s=320x180:d=3:r=15", "-f", "lavfi", "-i", "color=c=blue:s=320x180:d=2",
                        "-filter_complex", "[0][1][2]concat=n=3:v=1:a=0,format=yuv420p", "-c:v", "libx264", str(cls.clip)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_frames_sheet_json(self):
        r = video_eyes.run(str(self.clip), str(Path(self.td.name) / "o"), n=8)
        self.assertTrue(r["ok"], r)
        d = json.loads(Path(r["frames_json"]).read_text(encoding="utf-8"))
        self.assertTrue(Path(r["sheet"]).exists())
        self.assertLessEqual(len(d["frames"]), 8)
        self.assertGreaterEqual(len(d["frames"]), 3)  # red, test pattern, blue are all different
        self.assertEqual([f["t"] for f in d["frames"]], sorted(f["t"] for f in d["frames"]))
        self.assertTrue(d["local_only"])

    def test_dedupe_static(self):
        solid = Path(self.td.name) / "solid.mp4"
        subprocess.run([FF["path"], "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=green:s=320x180:d=4", "-pix_fmt", "yuv420p", str(solid)], check=True)
        r = video_eyes.run(str(solid), str(Path(self.td.name) / "s"), n=24)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["frames"], 1)

    def test_cap_and_range(self):
        r = video_eyes.run(str(self.clip), str(Path(self.td.name) / "r"), n=999, start=2, end=5)
        d = json.loads(Path(r["frames_json"]).read_text(encoding="utf-8"))
        self.assertLessEqual(d["max"], 60)
        self.assertTrue(all(2 <= f["t"] <= 5 for f in d["frames"]))

    def test_rejects_url_and_missing(self):
        self.assertFalse(video_eyes.run("https://example.com/a.mp4")["ok"])
        self.assertFalse(video_eyes.run("nope.mp4")["ok"])

    def test_subs_asks_first(self):
        if ensure._importable("faster_whisper"):
            self.skipTest("faster-whisper present")
        audio = Path(self.td.name) / "a.mp4"
        subprocess.run([FF["path"], "-loglevel", "error", "-y", "-i", str(self.clip), "-f", "lavfi", "-i", "sine=d=7", "-c:v", "copy", "-c:a", "aac", "-shortest", str(audio)], check=True)
        r = video_eyes.run(str(audio), str(Path(self.td.name) / "u"), subs=True)
        self.assertTrue(r["ok"])
        self.assertIn("설치할까요", r["prompt"])  # nothing installed without --yes


if __name__ == "__main__":
    unittest.main()
