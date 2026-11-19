# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Unit tests: storyboard.py, deliver.py, pipeline scoring in router_eval.py. No network.

Run: py tools/test_pipeline.py
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "skills" / "teacher-studio" / "scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sb = load("storyboard", STUDIO / "storyboard.py")
dv = load("deliver", STUDIO / "deliver.py")
ev = load("router_eval", ROOT / "tools" / "router_eval.py")


class StoryboardTests(unittest.TestCase):
    def test_slides_spec(self):
        d = {"title": "빛", "slides": [{"type": "title", "title": "빛 복습", "subtitle": "중2"}, {"type": "bullets", "title": "반사", "items": ["a", "b"], "note": "x"},
                                      {"type": "bignumber", "value": 3, "unit": "배", "caption": "c"}]}
        fr = sb.frames_from_spec(d)
        self.assertEqual([f["layout"] for f in fr], ["title", "bullets", "bignumber"])
        self.assertIn("발표 메모", fr[1]["note"])
        self.assertEqual(fr[2]["title"], "3배")

    def test_game_spec(self):
        d = json.loads((ROOT / "skills/teacher-game/assets/spec-examples/a-escape-light-wave.json").read_text(encoding="utf-8"))
        fr = sb.frames_from_spec(d)
        self.assertEqual(len(fr), 6)
        self.assertEqual(fr[2]["layout"], "locks")
        self.assertTrue(any("손맛" in f["note"] for f in fr))

    def test_shots_total_seconds(self):
        d = {"title": "30초", "shots": [{"title": "a", "seconds": 10, "narration": "n"}, {"title": "b", "seconds": "20"}]}
        fr = sb.frames_from_spec(d)
        self.assertEqual(sb.total_secs(fr), 30)
        self.assertIn("합계 30초", sb.render_text(fr, "x"))

    def test_generic_frames_and_unknown_layout(self):
        fr = sb.frames_from_spec({"frames": [{"title": "t", "note": "n", "layout": "weird"}, "plain"]})
        self.assertEqual(fr[0]["layout"], "list")
        self.assertEqual(fr[1]["title"], "plain")

    def test_empty_and_bad(self):
        self.assertEqual(sb.frames_from_spec({}), [])
        self.assertEqual(sb.frames_from_spec([1]), [])

    def test_html_is_offline_and_escaped(self):
        fr = sb.frames_from_spec({"frames": [{"title": "<script>alert(1)</script>", "note": "a&b"}]})
        out = sb.render_html(fr, "<b>x</b>")
        self.assertNotIn("<script>alert", out)
        self.assertNotIn("http://", out)
        self.assertNotIn("<script", out)
        self.assertIn("&lt;script&gt;", out)

    def test_palette_default(self):
        self.assertEqual(sb.palette("nonexistent-file.json")["bg"], sb.DEFAULT["bg"])

    def test_user_palette_file(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "pal.json"
            p.write_text(json.dumps({"colors": {"bg1": "#102030", "text": "#ffffff", "primary": "#ff8800"}}), encoding="utf-8")
            tok = sb.palette(str(p))
            self.assertEqual(tok["bg"], "#102030")
            self.assertEqual(tok["accent"], "#ff8800")


class DeliverTests(unittest.TestCase):
    def test_size_and_offline(self):
        with tempfile.TemporaryDirectory() as t:
            ok = Path(t) / "a.html"
            ok.write_text("<html><body>hi</body></html>", encoding="utf-8")
            bad = Path(t) / "b.html"
            bad.write_text('<img src="https://x.com/a.png">', encoding="utf-8")
            self.assertTrue(dv.offline_check(ok, "html")[0])
            self.assertFalse(dv.offline_check(bad, "html")[0])
            self.assertEqual(dv.human_size(2048), "2.0KB")
            out = dv.pack(ok, used=Path(t) / "none.json")
            self.assertIn("배포 꾸러미", out)
            self.assertIn("실명", out)
            self.assertIn("F11", out)

    def test_plain_link_is_not_external_resource(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "a.html"
            f.write_text('<a href="https://example.com">link</a>', encoding="utf-8")
            self.assertTrue(dv.offline_check(f, "html")[0])

    def test_url_validation(self):
        self.assertTrue(dv.valid_url("https://example.com/x"))
        self.assertFalse(dv.valid_url("javascript:alert(1)"))
        self.assertFalse(dv.valid_url("https://a b"))

    def test_qr(self):
        with tempfile.TemporaryDirectory() as t:
            svg = Path(t) / "q.svg"
            png = Path(t) / "q.png"
            if dv.find_qrcodegen() is None:
                self.skipTest("qrcodegen not bundled")
            self.assertIn("그렸어요", dv.make_qr("https://example.com/a", svg))
            self.assertTrue(svg.read_text(encoding="utf-8").startswith("<svg"))
            dv.make_qr("https://example.com/a", png)
            self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertIn("http", dv.make_qr("ftp://x", svg))

    def test_credit_line_recent_only(self):
        with tempfile.TemporaryDirectory() as t:
            u = Path(t) / "used.json"
            today = datetime.date(2026, 11, 19)
            u.write_text(json.dumps([{"name": "foo", "source": "bar", "license": "MIT", "date": "2026-11-18"},
                                     {"name": "old", "source": "x", "license": "MIT", "date": "2026-01-01"}]), encoding="utf-8")
            lines = dv.credit_lines(u, 7, today)
            self.assertEqual(lines, ["출처: foo (bar, MIT)"])
            self.assertEqual(dv.credit_lines(Path(t) / "missing.json"), [])

    def test_never_uploads(self):
        src = (STUDIO / "deliver.py").read_text(encoding="utf-8")
        for bad in ("urllib.request", "requests", "socket", "http.client", "smtplib"):
            self.assertNotIn("import " + bad, src)


class PipelineScoreTests(unittest.TestCase):
    CASE = {"id": "p", "request": "r", "route": ["slides"], "direction": None, "max_questions": 5, "must_not": [],
            "pipeline": {"checkpoint": "plan", "skips": ["storyboard"], "artifact": "options"}}

    def base(self, **kw):
        o = {"route": "slides", "shows_options_first": True, "question_count": 1, "first_reply": "x", "checkpoint": "plan", "skipped_stages": ["storyboard"], "artifact": "options"}
        o.update(kw)
        return o

    def test_full_marks(self):
        self.assertEqual(ev.score(self.CASE, self.base())["score"], 1.0)

    def test_wrong_checkpoint_loses_pipeline_part(self):
        r = ev.score(self.CASE, self.base(checkpoint="none"))
        self.assertLess(r["score"], 1.0)
        self.assertIn("pipeline", r["parts"])

    def test_non_pipeline_case_unchanged(self):
        c = {"id": "x", "request": "r", "route": ["slides"], "direction": None, "max_questions": 5, "must_not": []}
        self.assertEqual(ev.score(c, {"route": "slides", "first_reply": ""})["score"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
