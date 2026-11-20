#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Tests for sound_ears.py with earshot absent or mocked. Run: py shared/tools/test_sound_ears.py"""
import math
import os
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ensure
import sound_ears as se


def make_wav(path, seconds=1.0, amp=0.3, freq=440, sr=22050, clip=False):
    n = int(sr * seconds)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(sr)
        fr = []
        for i in range(n):
            v = amp * math.sin(2 * math.pi * freq * i / sr)
            v = max(-1.0, min(1.0, v * (4 if clip else 1)))
            fr.append(int(v * 32767))
        w.writeframes(struct.pack("<%dh" % n, *fr))


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.p1 = patch = mock.patch.object(se, "earshot_path", return_value="")
        self.p1.start()

    def tearDown(self):
        mock.patch.stopall()

    def test_good_clip_ok_without_earshot(self):
        f = Path(self.d) / "a.wav"
        make_wav(f, 1.0, 0.25)
        r = se.listen(str(f))
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "basic")
        self.assertIn("교실에서 써도 괜찮아요.", r["lines"])
        self.assertTrue(any("설치" in x for x in r["lines"]))   # offers install

    def test_clipping_and_loud_flagged(self):
        f = Path(self.d) / "c.wav"
        make_wav(f, 1.0, 0.9, clip=True)
        r = se.listen(str(f))
        txt = " ".join(r["lines"])
        self.assertIn("찌그러져요", txt)
        self.assertIn("고친 뒤에", txt)

    def test_quiet_and_long(self):
        f = Path(self.d) / "q.wav"
        make_wav(f, 5.0, 0.002)
        txt = " ".join(se.listen(str(f))["lines"])
        self.assertIn("너무 조용해요", txt)
        self.assertIn("효과음치고 길어요", txt)

    def test_missing_and_non_wav(self):
        self.assertFalse(se.listen(os.path.join(self.d, "none.wav"))["ok"])
        m = Path(self.d) / "x.mp3"
        m.write_bytes(b"x")
        r = se.listen(str(m))
        self.assertFalse(r["ok"])
        self.assertTrue(any("설치" in x for x in r["lines"]))

    def test_sfx_falls_back_to_zzfx(self):
        r = se.sfx("정답 딩 소리", os.path.join(self.d, "o.wav"), 1)
        self.assertTrue(r["ok"])
        self.assertEqual(r["source"], "zzfx")
        self.assertEqual(r["sound"], "correct")
        self.assertFalse(Path(self.d, "o.wav").exists())

    def test_seconds_clamped_and_pick(self):
        self.assertEqual(se.pick_bank("휘익 하는 바람"), "whoosh_fast")
        self.assertEqual(se.pick_bank("아무 말"), "")

    def test_sfx_with_mocked_earshot(self):
        out = Path(self.d) / "s.wav"

        def fake(args, timeout=300):
            if args[:2] == ["sfx", "list"]:
                return True, "whoosh_fast/crisp\nwhoosh_fast/soft\n"
            if args[:2] == ["sfx", "render"]:
                make_wav(out, 1.0, 0.5)
                return True, "ok"
            return False, ""
        with mock.patch.object(se, "earshot_path", return_value="fake.exe"), mock.patch.object(se, "_run_earshot", side_effect=fake):
            r = se.sfx("휘익 넘어가는 소리", str(out), 1.0)
        self.assertEqual(r["source"], "earshot")
        self.assertEqual(r["sound"], "whoosh_fast/crisp")
        self.assertTrue(out.exists())

    def test_listen_with_mocked_measure_and_describe(self):
        f = Path(self.d) / "m.wav"
        make_wav(f, 1.0, 0.25)

        def fake(args, timeout=300):
            if args[0] == "measure":
                return True, '{"loudness": {"lufs": -20.5}, "true_peak_db": -3.0}'
            return True, '{"tags": [{"tag": "Beep"}, {"tag": "Tone"}]}'
        with mock.patch.object(se, "earshot_path", return_value="fake.exe"), mock.patch.object(se, "_run_earshot", side_effect=fake):
            r = se.listen(str(f))
        self.assertEqual(r["mode"], "earshot")
        self.assertEqual(r["lufs"], -20.5)
        self.assertIn("Beep", r["lines"][0])

    def test_permission_error_degrades(self):
        with mock.patch.object(se, "earshot_path", return_value="blocked.exe"), mock.patch("subprocess.run", side_effect=PermissionError("blocked")):
            ok, msg = se._run_earshot(["measure", "x"])
        self.assertFalse(ok)
        self.assertIn("보안", msg)

    def test_ensure_needs_consent_and_states_size(self):
        with mock.patch.object(ensure, "earshot_exe", return_value=""), mock.patch("subprocess.run") as run:
            r = ensure.ensure_earshot(consent=False)
        self.assertFalse(r["ok"])
        self.assertIn("GB", r["prompt"])
        self.assertIn("--uninstall", r["prompt"])
        run.assert_not_called()

    def test_uninstall_removes_dir(self):
        d = Path(self.d) / "es"
        (d / "cache").mkdir(parents=True)
        (d / "cache" / "m.bin").write_bytes(b"1")
        with mock.patch.object(ensure, "EARSHOT_DIR", d):
            r = ensure.uninstall_earshot()
        self.assertTrue(r["ok"])
        self.assertFalse(d.exists())

    def test_install_url_is_github_not_pypi(self):
        self.assertIn("github.com/Leonxlnx/earshot", ensure.EARSHOT_URL)


if __name__ == "__main__":
    unittest.main()
