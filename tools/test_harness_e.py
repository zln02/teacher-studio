# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Harness upgrade E (2026-11-23 training deck folded back in): preset E tokens and contrast, the ink-poster style, the motion vocabulary
(ES2017, final state when still), garnish (고명) planning / readability guard / Codex command form, the deck integration (big type only on
key slides, pen, pills, backdrops), the small-text auto-fix, the example-note placeholder fix, direction defaults for 일상·업무·수업,
and the reference-frame tool's pure parts.   Run: py tools/test_harness_e.py"""
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
SLIDES = ROOT / "skills" / "teacher-slides"
sys.path[:0] = [str(SLIDES / "scripts"), str(ROOT / "shared" / "design"), str(ROOT / "skills" / "teacher-studio" / "scripts"), str(ROOT / "tools")]
os.environ.setdefault("PYTHONUTF8", "1")
import design  # noqa: E402
import garnish  # noqa: E402
import preset_e  # noqa: E402
import styles  # noqa: E402

JS = ROOT / "shared" / "design" / "motion_e.js"


def _strip_js_strings(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', src)


class PresetE(unittest.TestCase):
    def test_every_text_pair_passes_in_dark_and_light(self):
        self.assertEqual(preset_e.text_issues(), [])
        self.assertLess(preset_e.contrast(preset_e.PALETTE["light"]["acc"], preset_e.PALETTE["light"]["bg"]), 4.5)   # why it is large-only
        self.assertIn("acc", preset_e.LARGE_ONLY["light"])

    def test_style_palette_is_valid_and_registered(self):
        st = styles.STYLES["ink-poster"]
        self.assertEqual(st["pal"], preset_e.style_palette())
        self.assertEqual(design.palette_issues("ink-poster", st["pal"]), [])
        self.assertEqual(st["name"], preset_e.NAME)
        self.assertNotIn("ink-poster", styles.SEEDED)                      # never a surprise pick
        self.assertNotIn("ink-poster", styles.WORLD_STYLE["generic"])

    def test_type_scale_keeps_the_slide_floor(self):
        self.assertGreaterEqual(min(v for k, v in preset_e.TYPE.items() if isinstance(v, int)), 28)
        self.assertEqual(len(preset_e.CARDS), 6)
        self.assertEqual(preset_e.GRID["cols"], 12)

    def test_css_and_motion_tokens(self):
        css = preset_e.css("light")
        self.assertIn("--e-acc:#E4502F", css)
        self.assertIn("--e-t-s:200ms", css)
        self.assertNotIn("box-shadow:0 ", css)                               # flat cards
        js = preset_e.motion_js()
        self.assertNotIn("/*E_TOKENS*/null", js)
        self.assertIn('"stagger": 45', js)


class MotionJs(unittest.TestCase):
    def test_es2017_and_no_library(self):
        src = JS.read_text(encoding="utf-8")
        code = _strip_js_strings(src)
        self.assertIsNone(re.search(r"\?\.(?!\d)|\?\?", code), "optional chaining / nullish in motion_e.js")
        self.assertNotIn("import ", code)
        self.assertNotIn("anime", code)
        for word in ("big", "pen", "note", "pills", "hl", "dot", "drag", "cursor"):
            self.assertIn(f"V.{word} =", src.replace('V["in"]', "V.in"), word)
        self.assertIn("function hud(", src)
        self.assertIn("prefers-reduced-motion", src)
        if shutil.which("node"):
            r = subprocess.run(["node", "--check", str(JS)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_scenes_end_on_the_result(self):
        src = JS.read_text(encoding="utf-8")
        self.assertIn('result(el, "play", at + T.gap)', src)        # drag scene
        self.assertIn('result(el, "play", at)', src)                # demo cursor

    def test_deck_runtime_calls_the_vocabulary(self):
        js = (SLIDES / "assets" / "deck" / "deck.js").read_text(encoding="utf-8")
        self.assertIn("TSE.step(sl, k, !!still)", js)
        self.assertIn("applyStep(sl, step, true)", js)             # back = final state


class Garnish(unittest.TestCase):
    def test_codex_command_form(self):
        cmd = garnish.command("p", "bg-calm", "ref.png")
        self.assertEqual(cmd[:5], ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write"])
        self.assertEqual(cmd[5:8], ["-i", "ref.png", "--"])         # `--` right after -i
        self.assertNotIn("-i", garnish.command("p", "x"))

    def test_plan_is_one_consistent_set_without_text(self):
        man = garnish.plan("가정통신문 안내", ("story", "calm"))
        self.assertEqual(sorted(man), ["bg-calm", "bg-story"])
        base = garnish.base_prompt()
        for v in man.values():
            self.assertTrue(v["prompt"].startswith(base))
            self.assertIn("no text", v["prompt"])
            self.assertIn("no faces", v["prompt"])
        with self.assertRaises(ValueError):
            garnish.plan("x", ("hero",))

    def test_readability_guard(self):
        self.assertTrue(garnish.skip_reason({"type": "table", "title": "t"}))
        self.assertTrue(garnish.skip_reason({"type": "bullets", "items": ["가" * 80] * 3}))
        self.assertTrue(garnish.skip_reason({"type": "statement", "text": "짧은 문장", "backdrop": "none"}))
        self.assertEqual(garnish.skip_reason({"type": "statement", "text": "짧은 문장"}), "")
        self.assertEqual(garnish.default_role({"type": "statement"}), "story")

    def test_code_backdrop_is_texture_only(self):
        svg = garnish.svg_backdrop("calm", 3)
        self.assertNotIn("<text", svg)
        self.assertNotIn("http://www.w3.org/1999/xlink", svg)
        self.assertNotRegex(svg, r"href=|https?://(?!www\.w3\.org/2000/svg)")
        self.assertEqual(svg, garnish.svg_backdrop("calm", 3))     # deterministic
        e = garnish.env()
        self.assertIn(e["mode"], ("codex", "code"))


class DeckIntegration(unittest.TestCase):
    def spec(self, **kw):
        s = {"purpose": "발표", "title": "회신율 보고", "design": {"style": "ink-poster"}, "garnish": {"mode": "code"},
             "slides": [{"type": "title", "title": "겨울방학 안내", "subtitle": "일정과 담당"},
                        {"type": "statement", "text": "알림 앱 발송이 **먼저**", "pen": [{"mark": "under", "text": "알림 앱", "note": "먼저"}]},
                        {"type": "bullets", "title": "준비할 것", "items": ["초안 검토: 학년부", "결재: 교감·교장", "발송: 알림 앱"], "pills": ["준비", "발송", "회신"], "pill": 1},
                        {"type": "table", "title": "담당", "columns": ["학년", "담당"], "rows": [["1학년", "부장"], ["2학년", "부장"]]},
                        {"type": "closing", "title": "질문은 교무기획부로"}]}
        s.update(kw)
        return s

    def build(self, spec):
        import deck
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        out = d / "deck.html"
        rep = deck.build_deck(spec, d, out, seed=5)
        self.assertTrue(rep["ok"], rep.get("errors"))
        return rep, out.read_text(encoding="utf-8")

    def test_e_deck_markup(self):
        rep, html = self.build(self.spec())
        self.assertEqual(rep["style"], "ink-poster")
        self.assertIn('<body class="e-motion">', html)
        self.assertTrue("window.TSE = (function" in html)
        body = "".join(re.findall(r'<section class="sl.*?</section>', html, re.S))
        self.assertEqual(len(re.findall(r'data-e="big"', body)), 2)         # title + statement only (key-message slides)
        self.assertIn('data-e="dot"', html)
        self.assertIn('data-e="pills" data-e-cur="1"', html)
        self.assertIn("data-e-marks=", html)
        self.assertIn("gx-story", html)
        sec = re.findall(r'<section class="sl[^"]*" id="s(\d+)" data-type="(\w+)"(.*?)</section>', html, re.S)
        table = [body for n, t, body in sec if t == "table"][0]
        self.assertNotIn("e-scene", table)                                    # dense slide: no picture behind it
        self.assertNotRegex(html, r"https?://(?!www\.w3\.org)[^\"' )]+\.(?:jpg|png|webp)")

    def test_other_styles_are_untouched_unless_asked(self):
        spec = self.spec(design={"style": "minimal-premium"})
        spec.pop("garnish")
        for s in spec["slides"]:
            s.pop("pen", None)
            s.pop("pills", None)
        rep, html = self.build(spec)
        self.assertNotIn('<body class="e-motion">', html)
        self.assertFalse("window.TSE = (function" in html)
        self.assertNotIn('data-e="', "".join(re.findall(r'<section class="sl.*?</section>', html, re.S)))

    def test_example_note_is_not_a_leftover_blank(self):
        import deck
        import placeholders as ph
        spec = {"title": "t", "slides": [{"type": "title", "title": "안내", "note": ph.EXAMPLE_NOTE_DECK}]}
        self.assertEqual(deck.placeholder_gate(spec)[0], [])
        self.assertEqual(ph.find(ph.EXAMPLE_NOTE_DECK), [])                 # one detector: build, web review and pptx_check
        self.assertTrue(ph.find("[학교명] 안내"))
        spec["slides"][0]["note"] = "[학교명] 확인"
        self.assertTrue(deck.placeholder_gate(spec)[0])


class SmallTextFix(unittest.TestCase):
    def test_floor_fix_css_and_idempotent_apply(self):
        import slides_review as sr
        small = [["p", 20.0, "작은 글", "#s3 > :nth-child(4) > :nth-child(1)"], ["p", 18.0, "또", "#s3 > :nth-child(4) > :nth-child(1)"], ["p", 22.0, "x"]]
        css = sr.floor_fix_css(small, 28)
        self.assertEqual(css, "#s3 > :nth-child(4) > :nth-child(1){font-size:28px!important;line-height:1.2}")
        html = "<html><head><title>x</title></head><body></body></html>"
        once = sr.apply_floor_fix(html, css)
        twice = sr.apply_floor_fix(once, css)
        self.assertEqual(once, twice)
        self.assertEqual(once.count('id="ts-floor-fix"'), 1)
        self.assertEqual(sr.apply_floor_fix(once, ""), html)

    def test_probe_records_a_path_and_build_asks_for_the_fix(self):
        src = (SLIDES / "scripts" / "slides_review.py").read_text(encoding="utf-8")
        self.assertIn("cssPath(e)", src)
        self.assertIn("--fix-small", (SLIDES / "scripts" / "deck.py").read_text(encoding="utf-8"))


class Direction(unittest.TestCase):
    def cov(self, req):
        import direction
        d = direction.build(req, {})
        return d, {c["key"]: c for c in d["coverage"]}

    def test_defaults_follow_who_is_asking(self):
        d, c = self.cov("교직원 회의 보고 PPT 만들어 줘")
        self.assertEqual(d["domain"], "work")
        self.assertEqual(c["purpose"]["recommended"], "회의·보고")
        self.assertNotIn("우리 반 학생", c["audience"]["options"])
        d, c = self.cov("가족 여행 사진으로 영상 만들어 줘")
        self.assertEqual(d["domain"], "daily")
        self.assertEqual(c["audience"]["recommended"], "가족")
        d, c = self.cov("수업 시작용 뭐 재밌는 거")
        self.assertEqual(d["domain"], "class")
        self.assertEqual(c["purpose"]["recommended"], "수업 도입")

    def test_no_signal_offers_all_three(self):
        for req in ("느낌 있게 발표자료", "보드게임 만들어 줘"):
            d, c = self.cov(req)
            self.assertIsNone(d["domain"])
            self.assertEqual(c["purpose"]["options"], ["수업·교육", "업무·회의", "일상·모임"])
            for k in ("purpose", "audience"):
                self.assertIn(c[k]["recommended"], c[k]["options"])
        self.assertEqual(self.cov("느낌 있게 발표자료")[1]["purpose"]["recommended"], "업무·회의")


class RefFrames(unittest.TestCase):
    def test_times_label_slug(self):
        import ref_frames as rf
        self.assertEqual(rf.times(10, count=4), [1.25, 3.75, 6.25, 8.75])
        t = rf.times(10, every=0.5, start=2, end=4)
        self.assertEqual((t[0], t[-1], len(t)), (2.0, 3.5, 4))
        self.assertLessEqual(len(rf.times(10000, every=0.01)), 240)
        self.assertEqual(rf.label(75.5), "01:15.50")
        self.assertEqual(rf.slug("https://x.org/a/clip.mp4?t=3"), "clip")
        src = (ROOT / "tools" / "ref_frames.py").read_text(encoding="utf-8")
        self.assertIn('channel="msedge"', src)
        self.assertNotIn("ffmpeg", src.split('"""', 2)[2])                 # no ffmpeg in the code


if __name__ == "__main__":
    unittest.main()
