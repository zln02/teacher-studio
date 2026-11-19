# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Unit tests: shell kit (shared/shell), anti AI-default-look check (shared/design/ai_look.py), storyboard mock screens, direction previews. No network.

Run: py tools/test_shell_kit.py
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "shared" / "design"
STUDIO = ROOT / "skills" / "teacher-studio" / "scripts"
sys.path.insert(0, str(DESIGN))
sys.path.insert(0, str(ROOT / "shared" / "shell"))
sys.path.insert(0, str(STUDIO))

import ai_look  # noqa: E402
import color_check  # noqa: E402
import design  # noqa: E402
import shell  # noqa: E402
import styles  # noqa: E402


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sb = load("storyboard_shell", STUDIO / "storyboard.py")
dr = load("direction_shell", STUDIO / "direction.py")

HOUSE_PAGE = ("<html><head><style>:root{--bg:#faf9f5;--ink:#141413;--accent:#d97757}body{background:var(--bg)}"
              "h1{font-family:'Tiempos','Noto Serif KR',serif}</style></head><body><h1>Hello</h1></body></html>")


class AiLookTests(unittest.TestCase):
    def test_house_combo_needs_all_three(self):
        self.assertTrue(ai_look.is_house("#faf9f5", ["#d97757"], "Noto Serif KR"))
        self.assertTrue(ai_look.is_house("#f0eee6", ["#1a1a1a", "#c15f3c"], "Georgia, serif"))
        self.assertFalse(ai_look.is_house("#faf9f5", ["#d97757"], "Noto Sans KR"))      # sans headline
        self.assertFalse(ai_look.is_house("#ffffff", ["#d97757"], "Noto Serif KR"))     # pure white is not cream
        self.assertTrue(ai_look.is_house("#faf9f5", ["#2f5bea"], "Noto Serif KR"))      # cream + serif: any accent
        self.assertFalse(ai_look.is_house("#14110f", ["#d97757"], "Noto Serif KR"))     # dark page

    def test_thresholds_edges(self):
        self.assertFalse(ai_look.is_clay("#a82920"))   # dancheong vermilion h~29: not clay
        self.assertFalse(ai_look.is_clay("#b08d3c"))   # ochre / gold h~86: not clay
        self.assertTrue(ai_look.is_clay("#bd5d3a"))
        self.assertTrue(ai_look.is_cream("#f5f0e8"))
        self.assertFalse(ai_look.is_cream("#fff1a8"))  # yellow, too colourful
        self.assertTrue(ai_look.is_serif("'Gowun Batang', serif"))
        self.assertFalse(ai_look.is_serif("'Noto Sans KR', sans-serif"))

    def test_html_detection_and_user_exemption(self):
        self.assertEqual(len(ai_look.check_html(HOUSE_PAGE)), 1)
        own = HOUSE_PAGE.replace("<body>", '<body data-user-design="1">')
        self.assertEqual(ai_look.check_html(own), [])
        self.assertEqual(ai_look.check_tokens({"colors": {"bg1": "#faf9f5", "primary": "#d97757"}, "fonts": {"display": "Noto Serif KR"}, "userPalette": True}), [])
        self.assertEqual(len(ai_look.check_tokens({"colors": {"bg1": "#faf9f5", "primary": "#d97757"}, "fonts": {"display": "Noto Serif KR"}})), 1)

    def test_gradient_emoji_tell(self):
        page = ("<style>body{background:#ffffff}.hero{background:linear-gradient(135deg,#6366f1,#a855f7);}</style>"
                "<body><h1>🚀 AI로 ✨ 수업을 🎉 바꿔요</h1></body>")
        self.assertIn(ai_look.gradient_line(), ai_look.check_html(page))
        self.assertEqual(ai_look.check_html(page.replace("🚀", "").replace("✨", "").replace("🎉", "")), [])

    def test_rides_along_in_every_checker(self):
        res = color_check.html_results(HOUSE_PAGE)
        self.assertTrue(any(lv == "WARN" and "AI 회사" in msg for lv, msg in res))
        ok = color_check.html_results(HOUSE_PAGE.replace("#d97757", "#2f5bea").replace("'Tiempos','Noto Serif KR',serif", "'Noto Sans KR',sans-serif"))
        self.assertFalse(any(lv == "WARN" for lv, _ in ok))

    def test_selection_never_defaults_to_house(self):
        data = design.load()
        pairs = {x["id"]: x for x in data["fonts"]["pairs"]}
        for name, p in data["palettes"].items():
            self.assertFalse(design.is_ai_house(p, pairs[p["font"]]["display"]), name)
        for use, mood, subj, seed in itertools.product(design.USES, ["", "따뜻함", "차분", "고급"], ["", "국어", "과학"], range(3)):
            tk = design.generate(subj, 5, mood, use, seed)
            self.assertEqual(ai_look.check_tokens(tk), [], (use, mood, subj, seed, tk["palette"]))
        for sid, s in styles.STYLES.items():
            self.assertFalse(ai_look.is_house(s["pal"]["bg1"], [s["pal"]["primary"], s["pal"]["accent"]], s["font"]), sid)
        for req in ("느낌 있게 발표자료", "따뜻한 학부모 총회 자료", "중2 과학 빛 복습 게임", "반 성적 분석 보고서"):
            for c in dr.build(req, {})["cards"]:
                self.assertFalse(ai_look.is_house(c["colors"]["bg1"], [c["colors"]["primary"], c["colors"]["accent"]], c["font"]), (req, c["style"]))

    def test_user_palette_still_wins(self):
        house = {"bg1": "#faf9f5", "text": "#141413", "primary": "#c15f3c", "accent": "#d97757"}
        tk = design.generate("", 5, "", "present", 0, palette_from={"colors": house})
        self.assertEqual(tk["colors"]["primary"], "#c15f3c")
        self.assertEqual(ai_look.check_tokens(tk), [])


class ShellTests(unittest.TestCase):
    def test_tokens_for_every_style_are_readable(self):
        for sid in list(styles.STYLES) + [None]:
            t = shell.tokens(sid)
            self.assertGreaterEqual(shell.contrast(t["ink"], t["bg"]), 4.5, sid)
            self.assertGreaterEqual(shell.contrast(t["on_primary"], t["primary"]), 4.5, sid)
            self.assertTrue(shell.pattern(t))

    def test_default_is_not_house(self):
        t = shell.tokens()
        self.assertFalse(ai_look.is_house(t["bg"], [t["primary"], t["accent"]], shell.font_stack(t)))

    def test_user_colours_win_and_bad_values_dropped(self):
        t = shell.tokens("neon-cyber", user={"bg1": "#ffffff", "primary": "#123456", "text": "red;}</style>"})
        self.assertEqual((t["bg"], t["primary"], t["own"]), ("#ffffff", "#123456", True))
        self.assertNotIn("</style>", shell.vars_style(t))

    def test_frames_icons_escape(self):
        t = shell.tokens("pastel-cute")
        for k in shell.KINDS:
            h = shell.frame(k, "<b>x</b>", t, label="<script>")
            self.assertIn("sk-%s" % k, h)
            self.assertNotIn("<script>", h)
        self.assertIn("<path", shell.icon("bulb"))
        self.assertEqual(shell.icon("no-such-icon"), shell.icon("sparkles"))
        self.assertNotIn("onload", shell.icon("bulb", color='" onload="x'))
        self.assertIn("&lt;b&gt;", shell.badge("<b>", t))
        self.assertEqual(shell.icon_for("빛의 반사"), "bulb")
        self.assertIn("<svg", shell.spot("trophy", t))
        ch = shell.character("a")
        self.assertIn("<svg", ch)
        self.assertNotIn("http", ch)

    def test_page_is_offline(self):
        h = shell.page("t", shell.frame("tv", shell.spot("bulb", shell.tokens()), shell.tokens()), embed=False)
        for bad in ("http://", "https://", "<script", "<img"):
            self.assertNotIn(bad, h)

    def test_licenses_present(self):
        self.assertIn("MIT License", (ROOT / "shared" / "shell" / "LICENSE-tabler.txt").read_text(encoding="utf-8"))
        self.assertIn("CC0", (ROOT / "shared" / "shell" / "characters" / "LICENSE-thumbs.txt").read_text(encoding="utf-8"))
        self.assertGreater(len(shell.icon_names()), 100)


class PreviewTests(unittest.TestCase):
    def test_storyboard_mock_screens(self):
        d = json.loads((ROOT / "skills/teacher-game/assets/spec-examples/a-escape-light-wave.json").read_text(encoding="utf-8"))
        fr = sb.frames_from_spec(d)
        out = sb.render_html(fr, "t", sb.palette("none.json"), sb.choose_style(d, "", "game"), "board", "game")
        self.assertEqual(out.count('class="sk-dev sk-board"'), len(fr))
        self.assertIn("m-lockrow", out)       # escape room drawn as locks, not boxes
        self.assertIn("sk-btn", out)
        for bad in ("http://", "https://", "<script", "<img"):
            self.assertNotIn(bad, out)

    def test_storyboard_slides_chart_and_quiz(self):
        spec = {"slides": [{"type": "chart", "title": "독서", "series": [{"data": [4, 8, 12]}]}, {"type": "quiz", "q": "Q?", "choices": ["a", "b", "c", "d"]}]}
        out = sb.render_html(sb.frames_from_spec(spec), "t", None, "nature-calm", "tv", "slides")
        self.assertIn("m-bars", out)
        self.assertIn("m-ans", out)

    def test_storyboard_own_palette(self):
        tok = dict(sb.DEFAULT, bg="#102030", ink="#ffffff", accent="#ff8800", _own=True)
        out = sb.render_html(sb.frames_from_spec({"frames": [{"title": "a"}]}), "t", tok)
        self.assertIn("--sk-pr:#ff8800", out)

    def test_direction_first_screens(self):
        for req, kind in (("중2 과학 빛 복습 게임", "game"), ("학부모 총회 발표자료 8장", "slides"), ("반 성적 분석 보고서", "data")):
            d = dr.build(req, {})
            h = dr.render_html(d["cards"], req, pitches={"A": "<b>추천</b>"}, kind=d["inferred"]["kind"])
            self.assertEqual(h.count('class="card"'), 3)
            self.assertEqual(h.count("sk-dev "), 3)
            self.assertIn("&lt;b&gt;추천", h)
            self.assertEqual(d["inferred"]["kind"], kind)
            self.assertEqual(len({c["style"] for c in d["cards"]}), 3)

    def test_sample_titles(self):
        self.assertEqual(dr.sample_title("학부모 총회 발표자료 8장", {}), "학부모 총회")
        self.assertEqual(dr.sample_title("반 성적 분석 보고서", {}), "반 성적 분석 보고서")
        self.assertEqual(dr.sample_title("중2 과학 빛 복습 게임", {}), "빛 복습")


if __name__ == "__main__":
    unittest.main(verbosity=1)
