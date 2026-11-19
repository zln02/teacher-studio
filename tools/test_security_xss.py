# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Regression tests: user text and AI-written flair must never become live HTML/JS in generated pages.

Builds class tools, games and decks with XSS payloads and checks that no new tag or event handler appears
(compared with a build of harmless text), and that normal text (Korean, emoji, quotes, &) is not double-escaped.

Run: py tools/test_security_xss.py
"""
from __future__ import annotations

import copy
import html.parser
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
P_TITLE = "</title><img src=x onerror=alert(1)>"
P_SCRIPT = "</script><script>alert(9)</script>"
P_SVG = '<svg onload=alert(2)>'
NORMAL = '한글 😀 "따옴표" \'작은\' A & B <수학>'


def load(name: str, path: Path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class Scan(html.parser.HTMLParser):
    """Counts live tags and event-handler attributes."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: dict[str, int] = {}
        self.handlers: list[str] = []
        self.scripts: list[str] = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        self.tags[tag] = self.tags.get(tag, 0) + 1
        self._in_script = tag == "script"
        for k, v in attrs:
            if k.startswith("on"):
                self.handlers.append(f"{tag}.{k}={v}")

    def handle_endtag(self, tag):
        self._in_script = False

    def handle_data(self, data):
        if self._in_script:
            self.scripts.append(data)


def scan(page: str) -> Scan:
    s = Scan()
    s.feed(page)
    return s


class Base(unittest.TestCase):
    def assertSafe(self, bad: str, good: str, tags=("img", "script", "style", "svg")):
        a, b = scan(bad), scan(good)
        self.assertEqual(a.handlers, b.handlers, "event handler injected")
        for tag in tags:
            self.assertEqual(a.tags.get(tag, 0), b.tags.get(tag, 0), f"extra <{tag}> injected")
        self.assertNotIn("alert(1)</script", bad)
        self.assertEqual(sum(1 for x in a.scripts if x.strip().startswith("alert(")), 0)


class ClassToolTests(Base):
    @classmethod
    def setUpClass(cls):
        cls.bt = load("build_tool_t", SK / "teacher-class-tools" / "scripts" / "build_tool.py")

    def build(self, title, tool="timer"):
        spec = {"tool": tool, "title": title}
        if tool == "timer":
            spec["seconds"] = 300
        return self.bt.build(spec, fonts=False)[0]

    def test_title_payload(self):
        for payload in (P_TITLE[:30], "</title><img src=x onerror=alert(1)>", "<svg onload=alert(2)>"):
            self.assertSafe(self.build(payload), self.build("안전한 제목"))
        self.assertNotIn("</title><img", self.build(P_TITLE))

    def test_script_payload_in_title_and_data(self):
        bad = self.build(P_SCRIPT)
        self.assertSafe(bad, self.build("안전"))
        self.assertEqual(bad.count("</script>"), self.build("안전").count("</script>"))

    def test_normal_text_not_double_escaped(self):
        page = self.build('가나다 & "A" 😀')
        self.assertIn("<title>가나다 &amp; &quot;A&quot; 😀</title>", page)
        self.assertNotIn("&amp;amp;", page)


class GameTests(Base):
    SPEC = {"mechanic": "quiz", **json.loads((ROOT / "docs" / "examples" / "quiz-solar-system.json").read_text(encoding="utf-8"))}

    def build(self, spec: dict) -> str:
        with tempfile.TemporaryDirectory() as td:
            sp, out = Path(td) / "s.json", Path(td) / "o.html"
            sp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SK / "teacher-game" / "scripts" / "build.py"), "--spec", str(sp), "--out", str(out),
                                "--seed", "7", "--no-check", "--no-fonts"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env={**__import__("os").environ, "PYTHONUTF8": "1"})
            self.assertTrue(out.exists(), r.stdout + r.stderr)
            return out.read_text(encoding="utf-8")

    def mutated(self, **over):
        s = copy.deepcopy(self.SPEC)
        for k, v in over.items():
            if k == "q":
                s["items"][0]["q"] = v
            elif k == "choice":
                s["items"][0]["choices"][0] = v
            elif k == "exp":
                s["items"][0]["exp"] = v
            else:
                s[k] = v
        return s

    def test_title_and_items(self):
        good = self.build(self.SPEC)
        bad = self.build(self.mutated(title=P_TITLE, subtitle=P_SCRIPT, q=P_SCRIPT, choice=P_TITLE, exp=P_SCRIPT))
        self.assertSafe(bad, good)
        self.assertNotIn("</title><img", bad)
        self.assertNotIn("<script>alert(9)", bad)

    def test_normal_text(self):
        page = self.build(self.mutated(title='퀴즈 & "쇼" 😀'))
        self.assertIn("<title>퀴즈 &amp; &quot;쇼&quot; 😀</title>", page)
        self.assertNotIn("&amp;amp;", page)
        self.assertIn("\u0026", page)  # '&' inside inline JSON is &, which JS turns back into '&'

    def test_custom_flair_is_sanitized(self):
        import io
        bg = load("build_game_t", SK / "teacher-game" / "scripts" / "build.py")
        svg = bg.sanitize_svg('<svg xmlns="http://www.w3.org/2000/svg" onload="alert(2)"><script>alert(3)</script><circle r="4" onclick=alert(4) />'
                              '<a href="javascript:alert(5)"><foreignObject><div/></foreignObject></a></svg>')
        for bad in ("<script", "onload", "onclick", "javascript:", "foreignObject"):
            self.assertNotIn(bad.lower(), svg.lower())
        self.assertIn("<circle", svg)
        css = bg.sanitize_css("a{color:red}</style><script>alert(6)</script>@import 'x';b{width:expression(alert(7))}")
        self.assertNotIn("<", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("expression", css)
        self.assertIn("a{color:red}", css)


class StageTests(Base):
    """shared/stage/build_stage.py (motion + slides) and the slides builder."""

    def test_stage_title_and_doc(self):
        bs = load("build_stage_t", ROOT / "shared" / "stage" / "build_stage.py")
        with tempfile.TemporaryDirectory() as td:
            outs = []
            for title in ("안전", P_TITLE + P_SCRIPT):
                out = Path(td) / "o.html"
                bs.build({"title": title, "skin": "x"}, "/* show */", out, "", [], False, False, False, "", False)
                outs.append(out.read_text(encoding="utf-8"))
        self.assertSafe(outs[1], outs[0])
        self.assertNotIn("</title><img", outs[1])

    def test_deck_text(self):
        deck = load("deck_t", SK / "teacher-slides" / "scripts" / "deck.py")
        base = ROOT / "docs" / "examples"
        raw = json.loads((base / "slides-photosynthesis.json").read_text(encoding="utf-8"))
        pages = []
        for payload in (None, "</title><img src=x onerror=alert(1)>"):
            spec = copy.deepcopy(raw)
            if payload:
                spec["title"] = payload
                for it in spec["items"]:
                    for k in ("title", "q", "subtitle", "hint", "note"):
                        if k in it:
                            it[k] = payload
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / "d.html"
                rep = deck.build_deck(spec, base, out, seed=3)
                self.assertTrue(rep["ok"], rep)
                pages.append(out.read_text(encoding="utf-8"))
        self.assertSafe(pages[1], pages[0], tags=("img", "script", "style"))
        self.assertNotIn("<img src=x", pages[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
