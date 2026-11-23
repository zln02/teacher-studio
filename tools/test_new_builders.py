# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Builders found missing while making the 2026-11-22 showcase: teacher-motion event-promo (30 s kinetic opening / promo) and the
teacher-class-tools multi-tool class page (tabs); plus the adapted motion prompt references (MIT, attributed).
Run: py tools/test_new_builders.py"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOTION = ROOT / "skills" / "teacher-motion"
TOOLS = ROOT / "skills" / "teacher-class-tools"
os.environ.setdefault("PYTHONUTF8", "1")


def run(args):
    return subprocess.run([sys.executable] + [str(a) for a in args], capture_output=True, text=True, encoding="utf-8", errors="replace")


class EventPromo(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_missile_parts(self):
        m = MOTION / "assets" / "missiles" / "event-promo"
        for f in ("README.md", "show.js", "style.css", "skins/festival.json"):
            self.assertTrue((m / f).is_file(), f)
        js = (m / "show.js").read_text(encoding="utf-8")
        self.assertIn("S.timeline(tl, TOTAL)", js)          # MP4 / seek-able
        self.assertIn("function heroSrc()", js)            # no picture -> a drawn stand-in, nothing fetched
        self.assertNotRegex(js, r"\?\.(?!\d)|\?\?")
        skin = json.loads((m / "skins" / "festival.json").read_text(encoding="utf-8"))
        self.assertNotIn("노안", json.dumps(skin, ensure_ascii=False))   # example values only

    def test_builds_offline_with_and_without_a_picture(self):
        out = self.d / "a.html"
        r = run([MOTION / "scripts" / "build_stage.py", "--missile", "event-promo", "--skin", "festival", "--out", out, "--no-fonts"])
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertNotRegex(out.read_text(encoding="utf-8"), r"src=[\"']https?://")
        pic = self.d / "poster.png"
        pic.write_bytes(bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                                      "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"))
        (self.d / "c.json").write_text(json.dumps({"title": "체육대회", "hero": "poster.png"}, ensure_ascii=False), encoding="utf-8")
        out2 = self.d / "b.html"
        r = run([MOTION / "scripts" / "build_stage.py", "--missile", "event-promo", "--skin", "festival", "--content", self.d / "c.json", "--out", out2, "--no-fonts"])
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        h = out2.read_text(encoding="utf-8")
        self.assertIn("data:image/png;base64,", h)          # the file went INTO the page
        self.assertIn("체육대회", h)

    def test_routed_and_referenced(self):
        sk = (MOTION / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`event-promo`", sk)
        self.assertIn("references/motion-prompts.md", sk)


class ClassToolSet(unittest.TestCase):
    def test_tabs_page(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        out = d / "set.html"
        r = run([TOOLS / "scripts" / "build_tool.py", "--spec", TOOLS / "assets" / "spec-examples" / "f-set-class.json", "--out", out, "--no-check", "--no-fonts"])
        self.assertEqual(r.returncode, 0, r.stdout[-400:])
        h = out.read_text(encoding="utf-8")
        self.assertEqual(h.count("<iframe class=\"pane"), 3)
        for w in ("발표 순서 뽑기", "모둠 나누기", "타이머"):
            self.assertIn(w, h)
        self.assertNotRegex(h.replace("http://www.w3.org", ""), r"https?://")
        self.assertNotRegex(re.findall(r"<script>(.*?)</script>", h, re.S)[-1], r"\?\.(?!\d)|\?\?")

    def test_bad_set_fails(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        sp = d / "s.json"
        sp.write_text(json.dumps({"tool": "set", "tools": [{"tool": "timer"}]}), encoding="utf-8")
        r = run([TOOLS / "scripts" / "build_tool.py", "--spec", sp, "--out", d / "x.html", "--no-check", "--no-fonts"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("2-4", r.stdout)


class MotionPrompts(unittest.TestCase):
    def test_adapted_and_attributed(self):
        ref = (MOTION / "references" / "motion-prompts.md").read_text(encoding="utf-8")
        self.assertIn("MIT License", ref)
        self.assertIn("yihui-dev/awesome-opus5-5-videos", ref)
        self.assertGreaterEqual(ref.count("| @") + ref.count("@"), 5)
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("awesome-opus5-5-videos (yihui-dev, MIT License", notice)


if __name__ == "__main__":
    unittest.main()
